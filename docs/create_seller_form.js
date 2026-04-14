const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        AlignmentType, LevelFormat, HeadingLevel, BorderStyle, WidthType,
        ShadingType, VerticalAlign, PageBreak } = require('docx');
const fs = require('fs');

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const thickBorder = { style: BorderStyle.SINGLE, size: 8, color: "2E75B6" };

// 创建空行（可填写）
function createField(label, width = 9360) {
    return new Paragraph({
        spacing: { before: 120, after: 120 },
        children: [
            new TextRun({ text: label + ": ", bold: true, font: "Arial", size: 22 }),
            new TextRun({ text: "_______________________________________________", font: "Arial", size: 22 })
        ]
    });
}

// 创建勾选框
function createCheckbox(label, options = ["Ja", "Nej"]) {
    const boxes = options.map(opt => `[ ] ${opt}`).join("    ");
    return new Paragraph({
        spacing: { before: 60, after: 60 },
        children: [
            new TextRun({ text: label + ": ", bold: true, font: "Arial", size: 22 }),
            new TextRun({ text: boxes, font: "Arial", size: 22 })
        ]
    });
}

// Section标题
function createSection(title) {
    return new Paragraph({
        spacing: { before: 300, after: 120 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "2E75B6", space: 4 } },
        children: [
            new TextRun({ text: title, bold: true, font: "Arial", size: 26, color: "2E75B6" })
        ]
    });
}

// 两列表格（标签 + 填写区）
function createTableRow(label1, label2) {
    return new TableRow({
        children: [
            new TableCell({
                borders,
                width: { size: 4500, type: WidthType.DXA },
                shading: { fill: "F0F5F8", type: ShadingType.CLEAR },
                margins: { top: 80, bottom: 80, left: 120, right: 120 },
                children: [new Paragraph({
                    children: [new TextRun({ text: label1, font: "Arial", size: 20 })]
                })]
            }),
            new TableCell({
                borders,
                width: { size: 4500, type: WidthType.DXA },
                margins: { top: 80, bottom: 80, left: 120, right: 120 },
                children: [new Paragraph({
                    children: [new TextRun({ text: "________________________", font: "Arial", size: 20 })]
                })]
            }),
            new TableCell({
                borders,
                width: { size: 180, type: WidthType.DXA },
                shading: { fill: "F0F5F8", type: ShadingType.CLEAR },
                margins: { top: 80, bottom: 80, left: 60, right: 60 },
                children: [new Paragraph({
                    children: [new TextRun({ text: label2, font: "Arial", size: 20 })]
                })]
            }),
            new TableCell({
                borders,
                width: { size: 4180, type: WidthType.DXA },
                margins: { top: 80, bottom: 80, left: 120, right: 120 },
                children: [new Paragraph({
                    children: [new TextRun({ text: "________________________", font: "Arial", size: 20 })]
                })]
            })
        ]
    });
}

const doc = new Document({
    styles: {
        default: {
            document: { run: { font: "Arial", size: 22 } }
        }
    },
    sections: [{
        properties: {
            page: {
                size: { width: 11906, height: 16838 }, // A4
                margin: { top: 1134, right: 1134, bottom: 1134, left: 1134 }
            }
        },
        children: [
            // 标题
            new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { after: 200 },
                children: [
                    new TextRun({ text: "Sælgeroplysningsskema", bold: true, font: "Arial", size: 36, color: "2E75B6" })
                ]
            }),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { after: 400 },
                children: [
                    new TextRun({ text: "JOHN FRANDSEN VI HANDLER!", font: "Arial", size: 24 })
                ]
            }),

            // ========== 第1部分：基本信息 ==========
            createSection("1. Ejendommens oplysninger (Property Information)"),

            createField("Adresse (Address)"),
            createField("Postnr. / By (Postal Code / City)"),
            createField("Boligtype (Property Type)"),
            createField("Boligens størrelse i kvm (Property Size)"),
            createField("Grundens størrelse i kvm (Land Size)"),
            createField("Antal værelser (Number of Rooms)"),
            createField("Opført år (Year Built)"),

            createCheckbox("Ønskes til salg skilt (For Sale Sign)"),
            createCheckbox("Er der alarm på ejendommen (Alarm System)"),
            createField("Alarm kode (Alarm Code)"),

            // ========== 第2部分：设施 ==========
            createSection("2. Hårde hvidevarer (Appliances)"),

            createCheckbox("Komfur (Stove)"),
            createCheckbox("Ovn (Oven)"),
            createCheckbox("Kogeplader (Cooktop)", ["Induktion", "Keramisk", "Gas", "Træ"]),
            createCheckbox("Emhætte (Range Hood)"),
            createCheckbox("Køleskab (Refrigerator)"),
            createCheckbox("Køle/fryseskab (Fridge/Freezer)"),
            createCheckbox("Fryser (Freezer)", ["Kummefryser", "Skabsfryser"]),
            createCheckbox("Opvaskemaskine (Dishwasher)"),
            createCheckbox("Vaskemaskine (Washing Machine)"),
            createField("Fabrikat (Brand)"),
            createCheckbox("Tørretumbler (Dryer)"),
            createCheckbox("Mikrobølgeovn (Microwave)"),
            createCheckbox("Er der nogle defekter på nogle hårde hvidevarer? (Defects)"),
            createField("Hvis ja, hvilke (Which ones)"),

            // ========== 第3部分：窗户 ==========
            createSection("3. Vinduer (Windows)"),
            createCheckbox("Vinduestype (Window Type)", ["Træ", "Mahogni", "Træ/Alu", "Plastik", "Andet"]),
            createField("Årstal på vinduer (Year Windows Replaced)"),
            createField("Årstal på døre (Year Doors Replaced)"),

            // ========== 第4部分：装修 ==========
            createSection("4. Renovering (Renovation)"),
            createField("Årstal på gulve (Year Floors)"),
            createField("Årstal på køkken (Year Kitchen)"),
            createField("Årstal på badeværelse (Year Bathroom)"),
            createField("Hvis gulvarme, hvor? (Floor Heating Location)"),

            // ========== 第5部分：屋顶 ==========
            createSection("5. Tag (Roof)"),
            createField("Tagtype (Roof Type)"),
            createField("Årstal på tag (Year Roof Replaced)"),

            // ========== 第6部分：网络 ==========
            createSection("6. Internet / Antenneforhold (Internet)"),
            createCheckbox("Er det indlagt fiber? (Fiber Installed)"),
            createField("Mærke (Provider)"),
            createField("Årstal (Year)"),

            // ========== 第7部分：周边设施 ==========
            createSection("7. Institutioner (Nearby Facilities)"),
            createField("Nærmeste vuggestue (Nearest Nursery)"),
            createField("Nærmeste børnehave (Nearest Kindergarten)"),
            createField("Hvilken skole er man tilknyttet (School District)"),
            createCheckbox("Er der skolebus? (School Bus)"),
            createField("Hvis ja, hvor langt er der til stoppested? (Bus Stop Distance)"),

            // ========== 第8部分：能源 ==========
            createSection("8. Varmeforbrug (Heating Consumption)"),
            createField("Sælgers seneste årsforbrug (Last Year's Consumption)"),
            createField("Sælgers seneste årsforbrug i kr. (Last Year's Cost)"),
            new Paragraph({
                spacing: { before: 120, after: 200 },
                children: [
                    new TextRun({ text: "Vedhæft seneste års varmeforbrug (Attach heating records)", font: "Arial", size: 20, italics: true, color: "666666" })
                ]
            }),

            // ========== 第9部分：Grundejerforening ==========
            createSection("9. Grundejerforening (Homeowners Association)"),
            createCheckbox("Er der medlemspligtspligt? (Mandatory Membership)"),
            createField("Grundejerforeningens navn (HOA Name)"),
            createField("Formand (Chairman)"),
            createField("Tlf (Phone)"),
            createField("E-mail"),
            new Paragraph({
                spacing: { before: 120, after: 200 },
                children: [
                    new TextRun({ text: "Vedhæft dokumenter for grundejerforeningen (regnskab/budget, referater, vedtægter)", font: "Arial", size: 20, italics: true, color: "666666" })
                ]
            }),

            // ========== 第10部分：其他 ==========
            createSection("10. Øvrige forhold (Other Information)"),
            createField("Er ejendommen separatkloakeret? Hvis ja, hvornår? (Separate Sewage)"),
            createField("Er der i boligen en brændeovn? Hvis ja, hvad årstal? (Wood Stove)"),
            new Paragraph({
                spacing: { before: 120, after: 200 },
                children: [
                    new TextRun({ text: "Vedhæft dokumentation (Attach documentation)", font: "Arial", size: 20, italics: true, color: "666666" })
                ]
            }),

            // ========== 第11部分：卖方信息 ==========
            createSection("11. Sælgeroplysninger (Seller Information)"),
            createField("Fulde navn (Full Name)"),
            createField("CPR-nummer (CPR Number)"),
            createField("Tlf (Phone)"),
            createField("E-mail"),
            createField("Adresse (Address)"),
            new Paragraph({
                spacing: { before: 120, after: 200 },
                children: [
                    new TextRun({ text: "Vedhæft kopi af sygesikringsbevis OG kørekort/pas (Attach health card AND driver license/passport)", font: "Arial", size: 20, italics: true, color: "666666" })
                ]
            }),

            // ========== 第12部分：银行信息 ==========
            createSection("12. Oplysninger på sælgers bank (Bank Information)"),
            createField("Bankens navn (Bank Name)"),
            createField("Filialens adresse (Branch Address)"),
            createField("Bankrådgivers navn (Bank Advisor)"),
            createField("Bankrådgivers tlf (Advisor Phone)"),
            createField("Bankrådgivers e-mail"),

            // ========== 第13部分：保险 ==========
            createSection("13. Forsikringspolice (Insurance)"),
            createField("Forsikringsselskab (Insurance Company)"),
            new Paragraph({
                spacing: { before: 120, after: 200 },
                children: [
                    new TextRun({ text: "Vedhæft venligst den nuværende husforsikringspolice på huset (Attach current house insurance policy)", font: "Arial", size: 20, italics: true, color: "666666" })
                ]
            }),

            // ========== 签名 ==========
            createSection("14. Underskrift (Signature)"),
            new Paragraph({ spacing: { before: 200, after: 60 }, children: [] }),
            new Paragraph({
                children: [
                    new TextRun({ text: "Sælgeroplysningsskemaet er udfyldt af sælger.", font: "Arial", size: 22 })
                ]
            }),
            new Paragraph({ spacing: { before: 300, after: 60 }, children: [] }),
            createField("Dato (Date)"),
            new Paragraph({ spacing: { before: 200, after: 60 }, children: [] }),
            new Paragraph({
                children: [
                    new TextRun({ text: "Sælgers underskrift (Seller's Signature):", bold: true, font: "Arial", size: 22 })
                ]
            }),
            new Paragraph({
                spacing: { before: 400 },
                children: [
                    new TextRun({ text: "________________________________________________", font: "Arial", size: 22 })
                ]
            }),

            // 备注
            new Paragraph({ spacing: { before: 400 }, children: [] }),
            createSection("Bemærkninger (Additional Notes)"),
            new Paragraph({ spacing: { before: 200 }, children: [] }),
            new Paragraph({
                children: [new TextRun({ text: "_______________________________________________________________", font: "Arial", size: 22 })]
            }),
            new Paragraph({
                spacing: { before: 60 },
                children: [new TextRun({ text: "_______________________________________________________________", font: "Arial", size: 22 })]
            }),
            new Paragraph({
                spacing: { before: 60 },
                children: [new TextRun({ text: "_______________________________________________________________", font: "Arial", size: 22 })]
            })
        ]
    }]
});

Packer.toBuffer(doc).then(buffer => {
    fs.writeFileSync('/Users/weili/Downloads/丹麦买卖房子/John Frandsen/Sælgeroplysning_Udfyldelig.docx', buffer);
    console.log('Word文档创建成功！');
});
