#target photoshop
app.displayDialogs = DialogModes.NO;
if (app.documents.length === 0) {
    alert("Önce fotoğrafı Photoshop'ta açın.");
} else {
    var doc = app.activeDocument;
    var ratio = 50.0 / 60.0;
    var current = doc.width / doc.height;
    if (current > ratio) {
        var nw = doc.height * ratio;
        var left = (doc.width - nw) / 2;
        doc.crop([left, 0, left + nw, doc.height]);
    } else {
        var nh = doc.width / ratio;
        var top = (doc.height - nh) / 2;
        doc.crop([0, top, doc.width, top + nh]);
    }
    doc.resizeImage(UnitValue(50, "mm"), UnitValue(60, "mm"), 300, ResampleMethod.BICUBICSHARPER);
    try { doc.activeLayer.adjustBrightnessContrast(4, 3); } catch(e) {}
    alert("Biyometrik kadraj hazır: 50 x 60 mm / 300 ppi. Yüz ve arka planı son kez kontrol edin.");
}
