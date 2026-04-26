"""
Turso 数据库客户端 - SQLite 兼容适配层
用于 JobMatchAI 项目云端数据库持久化

用法：
  USE_LOCAL_SQLITE=true  → 本地 SQLite（开发模式）
  USE_LOCAL_SQLITE=false → Turso 云端（生产模式）
"""
import os
import sqlite3
import requests
from typing import Optional, List, Any, Iterable

# ── 加载 .env ──────────────────────────────────────────────
def _load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        for line in open(env_path):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                parts = line.split("=", 1)
                k = parts[0].strip()
                v = parts[1].strip()
                os.environ.setdefault(k, v)

_load_env()

TURSO_DB_URL = os.environ.get(
    "TURSO_DATABASE_URL",
    "https://jobmatchai-thorandloke.aws-eu-west-1.turso.io"
)
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "")
USE_LOCAL_SQLITE = os.environ.get("USE_LOCAL_SQLITE", "true").lower() == "true"

# ── 参数序列化 ───────────────────────────────────────────────
def _py_to_sqlite_value(v: Any) -> dict:
    """将 Python 值转为 Turso/Hrana Value 格式"""
    if v is None:
        return {"type": "null"}
    if isinstance(v, bool):
        return {"type": "integer", "value": "1" if v else "0"}
    if isinstance(v, int):
        return {"type": "integer", "value": str(v)}
    if isinstance(v, float):
        return {"type": "float", "value": v}
    if isinstance(v, bytes):
        import base64
        return {"type": "blob", "base64": base64.b64encode(v).decode()}
    return {"type": "text", "value": str(v)}


def _sqlite_to_py(val: dict) -> Any:
    """将 Turso/Hrana Value 格式转回 Python 值"""
    t = val.get("type", "")
    v = val.get("value")
    if t == "null":
        return None
    if t == "integer":
        return int(v)
    if t == "float":
        return float(v)
    if t == "text":
        return str(v)
    if t == "blob":
        import base64
        return base64.b64decode(v)
    return v


def _build_request(sql: str, params: tuple) -> dict:
    """
    构建 Turso HTTP execute 请求体。
    SQL 中的 ? 占位符转为 $1, $2 ...（美元符，0索引）
    """
    idx = 0
    sql_parts = []
    i = 0
    args = []
    while i < len(sql):
        if sql[i] == "?":
            sql_parts.append("$" + str(idx + 1))
            if idx < len(params):
                args.append(_py_to_sqlite_value(params[idx]))
            else:
                args.append({"type": "null"})
            idx += 1
        else:
            sql_parts.append(sql[i])
        i += 1
    return {
        "stmt": {
            "sql": "".join(sql_parts),
            "args": args,
            "want_rows": True,
        }
    }


# ── Cursor ─────────────────────────────────────────────────
class TursoCursor:
    """模拟 sqlite3.Cursor"""

    def __init__(self, conn: "TursoConnection"):
        self._conn = conn
        self._results: List[dict] = []
        self._lastrowid: Optional[int] = None
        self._rowcount: int = -1

    def execute(self, sql: str, params: Iterable[Any] = ()) -> "TursoCursor":
        sql = sql.strip()
        params = tuple(params)

        # PRAGMA 等本地操作走本地 SQLite
        if sql.upper().startswith("PRAGMA"):
            if USE_LOCAL_SQLITE:
                lc = self._conn._ensure_local().cursor()
                lc.execute(sql, params)
                self._results = [dict(row) for row in lc.fetchall()]
            return self

        resp = self._conn._exec(sql, params)
        self._parse_result(resp, sql)
        return self

    def _parse_result(self, resp: dict, sql: str):
        sql_up = sql.upper().strip()
        result = resp.get("result", {})
        if sql_up.startswith("SELECT"):
            cols = [c["name"] for c in result.get("cols", [])]
            rows_data = result.get("rows", [])
            self._results = [
                {col: _sqlite_to_py(cell) for col, cell in zip(cols, row)}
                for row in rows_data
            ]
            self._rowcount = len(self._results)
        else:
            self._lastrowid = result.get("last_insert_rowid")
            self._rowcount = result.get("affected_row_count", 0)
            self._results = []

    def fetchone(self) -> Optional[dict]:
        if self._results:
            return self._results.pop(0)
        return None

    def fetchall(self) -> List[dict]:
        rows = self._results
        self._results = []
        return rows

    def fetchmany(self, size: int = 1) -> List[dict]:
        result = self._results[:size]
        self._results = self._results[size:]
        return result

    @property
    def lastrowid(self) -> Optional[int]:
        return self._lastrowid

    @property
    def rowcount(self) -> int:
        return self._rowcount


# ── Connection ─────────────────────────────────────────────
class TursoConnection:
    """模拟 sqlite3.Connection，走 Turso /v1/execute HTTP API"""

    def __init__(self, url: str, auth_token: str):
        self.url = url.rstrip("/")
        self.auth_token = auth_token
        self.__local: Optional[sqlite3.Connection] = None

    def _ensure_local(self) -> sqlite3.Connection:
        if self.__local is None:
            db_path = os.path.join(os.path.dirname(__file__), "data", "jobmatchai.db")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            self.__local = sqlite3.connect(db_path, check_same_thread=False)
            self.__local.row_factory = sqlite3.Row
        return self.__local

    def _exec(self, sql: str, params: tuple) -> dict:
        payload = _build_request(sql, params)
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = "Bearer " + self.auth_token
        resp = requests.post(
            self.url + "/v1/execute",
            headers=headers,
            json=payload,
            timeout=30,
        )
        if resp.status_code >= 400:
            raise RuntimeError(
                "Turso " + str(resp.status_code) + ": " + resp.text[:300]
            )
        return resp.json()

    def execute(self, sql: str, params: Iterable[Any] = ()) -> TursoCursor:
        return TursoCursor(self).execute(sql, params)

    def executemany(self, sql: str, params_list: Iterable[Iterable[Any]]):
        for params in params_list:
            self.execute(sql, params)

    def commit(self):
        if self.__local:
            self.__local.commit()

    def rollback(self):
        if self.__local:
            self.__local.rollback()

    def close(self):
        if self.__local:
            self.__local.close()
            self.__local = None

    def cursor(self) -> TursoCursor:
        return TursoCursor(self)


# ── 主入口 ─────────────────────────────────────────────────
def get_turso_connection(
    url: Optional[str] = None,
    auth_token: Optional[str] = None,
) -> TursoConnection:
    url = url or TURSO_DB_URL
    token = auth_token or TURSO_AUTH_TOKEN
    return TursoConnection(url, token)


def get_db_connection() -> Any:
    """
    主入口。
    USE_LOCAL_SQLITE=true  → 本地 SQLite（开发）
    USE_LOCAL_SQLITE=false → Turso 云端（生产）
    """
    if USE_LOCAL_SQLITE:
        db_path = os.path.join(os.path.dirname(__file__), "data", "jobmatchai.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    return get_turso_connection()
