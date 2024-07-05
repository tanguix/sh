
import jsPDF from "jspdf";
import { Base64Font } from "$lib/components/data/font.ts";



// ----------------- of course later need more refinement and comments, as well as adding the invoice part -----------------



// Load the custom base64 font into the jsPDF document
export function loadBase64Font(doc: jsPDF) {
    doc.addFileToVFS("NotoSerifSC-Light.ttf", Base64Font);
    doc.addFont("NotoSerifSC-Light.ttf", "NotoSerifSC", "normal");
    doc.setFont("NotoSerifSC");
}

// Add an image to the PDF document
export async function addImageToPDF(doc: jsPDF, imageUrl: string, x: number, y: number, maxWidth: number, maxHeight: number) {
    return new Promise<void>((resolve, reject) => {
        const img = new Image();
        img.crossOrigin = "Anonymous";
        img.onload = function() {
            const ratio = Math.min(maxWidth / img.naturalWidth, maxHeight / img.naturalHeight);
            const newWidth = img.naturalWidth * ratio;
            const newHeight = img.naturalHeight * ratio;

            const canvas = document.createElement('canvas');
            canvas.width = img.naturalWidth;
            canvas.height = img.naturalHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, img.naturalWidth, img.naturalHeight);

            const imgData = canvas.toDataURL('image/jpeg');
            doc.addImage(imgData, 'JPEG', x, y, newWidth, newHeight);
            resolve();
        };
        img.onerror = function() {
            reject(new Error('Image could not be loaded'));
        };
        img.src = imageUrl;
    });
}

// Generate a PDF document from the results
export async function generatePDF(results: any[], content: string) {
    const doc = new jsPDF('p', 'mm', 'a4');
    loadBase64Font(doc);
    doc.setFontSize(7);

    let currentY = 10;
    const margin = 10;
    const imgMaxWidth = 70;
    const imgMaxHeight = imgMaxWidth * 3 / 4;
    const textWidth = 80;

    for (const result of results) {
        if (result.image_url) {
            await addImageToPDF(doc, result.image_url, margin + textWidth + margin, currentY, imgMaxWidth, imgMaxHeight);
        }

        doc.text(content, margin, currentY);

        let blockHeight = imgMaxHeight + margin;
        currentY += blockHeight;

        if (currentY + blockHeight > doc.internal.pageSize.getHeight() - margin) {
            doc.addPage();
            currentY = 10;
        }
    }

    doc.save("results.pdf");
}
