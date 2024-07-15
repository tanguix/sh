



<script lang='ts'>


// TODO: style the one like stripe company had (save in the root for references)

// importing the company logo PNG 
import logoPng from './png/logo.png'; // Adjust the path to your PNG file
import jsPDF from 'jspdf';

function drawTableLines(
    doc: jsPDF, 
    leftMargin: number, 
    rightMargin: number, 
    headerY: number, 
    subHeaderY: number, 
    firstRowY: number, 
    bottomY: number, 
    rowHeight: number, 
    columnPositions: number[]
) {
    doc.setDrawColor(220, 220, 220);
    doc.setLineWidth(0.25);

    doc.line(leftMargin, headerY, rightMargin, headerY);
    doc.line(leftMargin, subHeaderY, rightMargin, subHeaderY);
    for (let y = firstRowY; y <= bottomY; y += rowHeight) {
        doc.line(leftMargin, y, rightMargin, y);
    }

    doc.line(leftMargin, headerY, leftMargin, bottomY);
    doc.line(rightMargin, headerY, rightMargin, bottomY);

    columnPositions.forEach(pos => {
        doc.line(pos, headerY, pos, bottomY);
    });
}

function drawTableHeader(
    doc: jsPDF, 
    columns: any[], 
    leftMargin: number, 
    baseWidth: number, 
    subHeaderY: number, 
    headerFontSize: number
) {
    doc.setDrawColor(0, 0, 0);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(headerFontSize);

    let columnStart = leftMargin;
    columns.forEach(column => {
        const columnEnd = columnStart + column.width * baseWidth;
        const columnCenter = (columnStart + columnEnd) / 2;
        const textWidth = doc.getTextWidth(column.name);

        doc.text(column.name, columnCenter - textWidth / 2, subHeaderY - 5);

        columnStart = columnEnd;
    });
}

function drawTableRows(
    doc: jsPDF, 
    rows: any[], 
    columns: any[], 
    leftMargin: number, 
    baseWidth: number, 
    firstRowY: number, 
    rowHeight: number, 
    rowFontSize: number
) {
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(rowFontSize);

    rows.forEach((row, rowIndex) => {
        let columnStart = leftMargin;
        columns.forEach(column => {
            const columnEnd = columnStart + column.width * baseWidth;
            const columnCenter = (columnStart + columnEnd) / 2;
            const cellText = row[column.name];
            const textWidth = doc.getTextWidth(cellText);

            doc.text(cellText, columnCenter - textWidth / 2, firstRowY + rowIndex * rowHeight - 5);

            columnStart = columnEnd;
        });
    });
}

function drawTotalRow(
    doc: jsPDF, 
    rows: any[], 
    columns: any[], 
    leftMargin: number, 
    baseWidth: number, 
    bottomY: number, 
    rowFontSize: number
) {
    const totalQuantities = rows.reduce((acc, row) => acc + parseInt(row['QUANTITIES']), 0);
    const totalPrices = rows.reduce((acc, row) => acc + parseInt(row['TOTAL']), 0);

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(rowFontSize);

    const totalRowY = bottomY - 5;
    const firstColumnWidth = columns[0].width * baseWidth;
    const totalColumnCenter = leftMargin + firstColumnWidth / 2;
    const totalTextWidth = doc.getTextWidth('TOTAL');
    doc.text('TOTAL', totalColumnCenter - totalTextWidth / 2, totalRowY);

    let columnStart = leftMargin + firstColumnWidth + columns[1].width * baseWidth + columns[2].width * baseWidth;
    columns.slice(3).forEach((column, colIndex) => {
        const columnEnd = columnStart + column.width * baseWidth;
        const columnCenter = (columnStart + columnEnd) / 2;
        const cellText = colIndex === 0 ? totalQuantities.toString() : (colIndex === 2 ? totalPrices.toString() : '');
        const textWidth = doc.getTextWidth(cellText);

        doc.text(cellText, columnCenter - textWidth / 2, totalRowY);

        columnStart = columnEnd;
    });
}

function drawPayToAndFromSections(
  doc: jsPDF,
  leftMargin: number,
  fromY: number,
  payToY: number,
  pageWidth: number,
  labelSpacing: number,
  lineSpacing: number = 5, // Line spacing within sections
  sectionSpacing: number = 10 // Spacing between "FROM" and "PAY TO" sections
) {
  const labelWidth = doc.getTextWidth('PAY TO:');
  const addressWidth = doc.getTextWidth('Avery Davis123 Anywhere St., Any City123 456 7890');

  const fromLines = [
    { label: 'FROM:', address: 'Really Great Company' },
    { label: '', address: '123 Main St., Anytown USA' },
    { label: '', address: '12345' }
  ];

  const payToLines = [
    { label: 'PAY TO:', address: 'Avery Davis' },
    { label: '', address: '123 Anywhere St., Any City' },
    { label: '', address: '123 456 7890' }
  ];

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(10);

  let currentY = fromY;
  fromLines.forEach(({ label, address }) => {
    doc.text(label, leftMargin, currentY);
    doc.text(address, pageWidth - leftMargin - addressWidth - labelSpacing, currentY);
    currentY += lineSpacing; // Adjust the line spacing as needed
  });

  currentY += sectionSpacing; // Add spacing between the sections

  payToLines.forEach(({ label, address }) => {
    doc.text(label, leftMargin, currentY);
    doc.text(address, pageWidth - leftMargin - addressWidth - labelSpacing, currentY);
    currentY += lineSpacing;
  });
}

function drawInvoiceHeader(
  doc: jsPDF,
  invoiceNumber: string,
  date: string,
  pageWidth: number,
  leftMargin: number,
  topMargin: number,
  headerFontSize: number,
  invoiceNumberFontSize: number,
  dateFontSize: number
) {
  const maxWidth = pageWidth - leftMargin;
  const maxHeight = doc.internal.pageSize.getHeight();

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(headerFontSize);
  const headerText = 'INVOICE';
  const headerWidth = doc.getTextWidth(headerText);
  const headerX = pageWidth - leftMargin - headerWidth;
  const headerY = topMargin;

  if (headerX >= 0 && headerX <= maxWidth && headerY >= 0 && headerY <= maxHeight) {
    doc.text(headerText, headerX, headerY); // Position "INVOICE" header
  }

  doc.setFontSize(invoiceNumberFontSize);
  const invoiceNumberText = `#${invoiceNumber}`;
  const invoiceNumberWidth = doc.getTextWidth(invoiceNumberText);
  const invoiceNumberX = pageWidth - leftMargin - invoiceNumberWidth;
  const invoiceNumberY = headerY + invoiceNumberFontSize + 5; // Position invoice number below "INVOICE"

  if (invoiceNumberX >= 0 && invoiceNumberX <= maxWidth && invoiceNumberY >= 0 && invoiceNumberY <= maxHeight) {
    doc.text(invoiceNumberText, invoiceNumberX, invoiceNumberY);
  }

  doc.setFontSize(dateFontSize);
  const dateWidth = doc.getTextWidth(date);
  const dateX = pageWidth - leftMargin - dateWidth;
  const dateY = invoiceNumberY + dateFontSize + 5; // Position date below invoice number

  if (dateX >= 0 && dateX <= maxWidth && dateY >= 0 && dateY <= maxHeight) {
    doc.text(date, dateX, dateY);
  }
}

function drawNoteSection(
    doc: jsPDF,
    pageWidth: number,
    noteY: number, // New parameter to control vertical position
    noteFontSize: number,
    noteText: string,
    noteLineSpacing: number = 2
) {
    // Split the note text into lines that fit within the page width
    const maxTextWidth = pageWidth - 20; // Let's give some padding from both sides
    const noteLines = doc.splitTextToSize(noteText, maxTextWidth);

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(noteFontSize);

    let currentY = noteY;

    // Calculate the text width for the widest line
    const widestLineWidth = noteLines.reduce((maxWidth, line) => {
        const lineWidth = doc.getTextWidth(line);
        return Math.max(maxWidth, lineWidth);
    }, 0);

    // Determine the left margin to center the widest line
    const margin = (pageWidth - widestLineWidth) / 2;

    // Draw each line of text centered based on the calculated margin
    noteLines.forEach((line) => {
        const textWidth = doc.getTextWidth(line);
        const noteX = (pageWidth - textWidth) / 2; // Center each line with respect to the page width
        doc.text(line, noteX, currentY);
        currentY += noteFontSize + noteLineSpacing;
    });
}

function generateInvoice(columns: any[], rows: any[]) {
    const doc = new jsPDF();

    // Add the logo at the top center
    // ==========================================================================
    const pageWidth = doc.internal.pageSize.getWidth();
    const topMargin = 10; // Adjust this value to position the logo vertically

    const logoWidth = 50; // Adjust this value as needed
    const logoHeight = 50; // Adjust this value as needed
    const centerX = (pageWidth - logoWidth) / 2;
    doc.addImage(logoPng, 'PNG', centerX, topMargin, logoWidth, logoHeight);

    // Table's section
    const baseWidth = 10;
    const totalTableWidth = columns.reduce((acc, col) => acc + col.width * baseWidth, 0);
    const pageHeight = doc.internal.pageSize.getHeight();

    const leftMargin = (pageWidth - totalTableWidth) / 2;
    const rightMargin = leftMargin + totalTableWidth;
    const columnPositions = columns.map((column, index) => leftMargin + columns.slice(0, index).reduce((a, b) => a + b.width * baseWidth, 0));
    const columnWidths = columns.map(column => column.width * baseWidth);

    const tableHeaderY = 105;
    const subTableHeaderY = tableHeaderY + 10;
    const firstRowY = subTableHeaderY + 10;
    const rowHeight = 10;
    const rowBottomY = firstRowY + rows.length * rowHeight;

    const tableHeaderFontSize = Math.floor(rowHeight * 0.7);
    const rowFontSize = Math.floor(rowHeight * 0.6);

    drawTableLines(
        doc, 
        leftMargin, 
        rightMargin, 
        tableHeaderY, 
        subTableHeaderY, 
        firstRowY, 
        rowBottomY, 
        rowHeight, 
        columnPositions);

    const tableBottomY = firstRowY + rows.length * rowHeight;

    drawTableHeader(doc, columns, leftMargin, baseWidth, subTableHeaderY, tableHeaderFontSize);
    drawTableRows(doc, rows, columns, leftMargin, baseWidth, firstRowY, rowHeight, rowFontSize);
    drawTotalRow(doc, rows, columns, leftMargin, baseWidth, rowBottomY, rowFontSize);

    // From and To section
    const fromY = 40; // Adjust this value to position the whole section of "FROM" and "PAY TO"
    const payToY = 60; // Adjust this value to position the "PAY TO" section, but actually no effect
    const labelSpacing = 110; // spacing between HEADER and their value
    const lineSpacing = 6; // Adjust line spacing within VALUE of PAY TO or VALUE of FROM
    const sectionSpacing = 15; // Adjust spacing between "FROM" and "PAY TO" sections

    drawPayToAndFromSections(doc, leftMargin, fromY, payToY, pageWidth, labelSpacing, lineSpacing, sectionSpacing);

    // Invoice Header Section
    const headerFontSize = 20;
    const invoiceNumberFontSize = 12;
    const dateFontSize = 10;
    const headerTopMargin = 40; // Adjust this value to position the header section vertically
    const invoiceNumber = 'SDF00023'
    const invoiceDate = 'July 1, 2024'

    drawInvoiceHeader(
        doc,
        invoiceNumber,
        invoiceDate,
        pageWidth,
        leftMargin,
        headerTopMargin,
        headerFontSize,
        invoiceNumberFontSize,
        dateFontSize
    );

    const noteText = 'This is a note section. \nYou can write multiple lines of text here.';
    const noteFontSize = 10;
    const noteLineSpacing = 2;
    const noteTopSpacing = 20; // parameter to control spacing between table and note

    const noteY = tableBottomY + noteTopSpacing; // Position the note below the table with spacing

    drawNoteSection(doc, pageWidth, noteY, noteFontSize, noteText, noteLineSpacing);

    doc.save('invoice.pdf');
}

// set up the standard template for invoice table
const columns = [
    { name: 'PRODUCT REF', width: 3, offset: 0 },
    { name: 'DESCRIPTION', width: 5 },
    { name: 'H.S.CODE', width: 2 },
    { name: 'QUANTITIES', width: 3 },
    { name: 'UNIT PRICE', width: 3 },
    { name: 'TOTAL', width: 2 }
];

// Later pass the data into the function, the result parameter
// append the unit to quantities, handle in frontend input, and just pass that here as value
// export const results: any[] = [];

const rows = [
    { 'PRODUCT REF': 'PR001', 'DESCRIPTION': 'Product 1', 'H.S.CODE': '1234', 'QUANTITIES': '10', 'UNIT PRICE': '50', 'TOTAL': '500' },
    { 'PRODUCT REF': 'PR002', 'DESCRIPTION': 'Product 2', 'H.S.CODE': '5678', 'QUANTITIES': '20', 'UNIT PRICE': '30', 'TOTAL': '600' },
    { 'PRODUCT REF': 'PR003', 'DESCRIPTION': 'Product 3', 'H.S.CODE': '9101', 'QUANTITIES': '15', 'UNIT PRICE': '40', 'TOTAL': '600' },
    { 'PRODUCT REF': 'PR004', 'DESCRIPTION': 'Product 4', 'H.S.CODE': '1121', 'QUANTITIES': '5', 'UNIT PRICE': '100', 'TOTAL': '500' },
    { 'PRODUCT REF': 'PR005', 'DESCRIPTION': 'Product 5', 'H.S.CODE': '3141', 'QUANTITIES': '8', 'UNIT PRICE': '70', 'TOTAL': '560' },
    { 'PRODUCT REF': 'PR006', 'DESCRIPTION': 'Product 6', 'H.S.CODE': '3149', 'QUANTITIES': '7', 'UNIT PRICE': '41', 'TOTAL': '290' },
];

</script>

<button on:click={() => generateInvoice(columns, rows)}>Invoice</button>







<!-- <script lang='ts'> -->


<!--     // importing the company logo svg  -->
<!--     import SunIcon from './svg/SunIcon.svelte'; -->
<!--     import jsPDF from 'jspdf'; -->



<!--     function drawTableLines( -->
<!--         doc: jsPDF,  -->
<!--         leftMargin: number,  -->
<!--         rightMargin: number,  -->
<!--         headerY: number,  -->
<!--         subHeaderY: number,  -->
<!--         firstRowY: number,  -->
<!--         bottomY: number,  -->
<!--         rowHeight: number,  -->
<!--         columnPositions: number[] -->
<!--     ) { -->
<!--         doc.setDrawColor(220, 220, 220); -->
<!--         doc.setLineWidth(0.25); -->

<!--         doc.line(leftMargin, headerY, rightMargin, headerY); -->
<!--         doc.line(leftMargin, subHeaderY, rightMargin, subHeaderY); -->
<!--         for (let y = firstRowY; y <= bottomY; y += rowHeight) { -->
<!--             doc.line(leftMargin, y, rightMargin, y); -->
<!--         } -->

<!--         doc.line(leftMargin, headerY, leftMargin, bottomY); -->
<!--         doc.line(rightMargin, headerY, rightMargin, bottomY); -->

<!--         columnPositions.forEach(pos => { -->
<!--             doc.line(pos, headerY, pos, bottomY); -->
<!--         }); -->
<!--     } -->

<!--     function drawTableHeader( -->
<!--         doc: jsPDF,  -->
<!--         columns: any[],  -->
<!--         leftMargin: number,  -->
<!--         baseWidth: number,  -->
<!--         subHeaderY: number,  -->
<!--         headerFontSize: number -->
<!--     ) { -->
<!--         doc.setDrawColor(0, 0, 0); -->
<!--         doc.setFont('helvetica', 'bold'); -->
<!--         doc.setFontSize(headerFontSize); -->

<!--         let columnStart = leftMargin; -->
<!--         columns.forEach(column => { -->
<!--             const columnEnd = columnStart + column.width * baseWidth; -->
<!--             const columnCenter = (columnStart + columnEnd) / 2; -->
<!--             const textWidth = doc.getTextWidth(column.name); -->

<!--             doc.text(column.name, columnCenter - textWidth / 2, subHeaderY - 5); -->

<!--             columnStart = columnEnd; -->
<!--         }); -->
<!--     } -->

<!--     function drawTableRows( -->
<!--         doc: jsPDF,  -->
<!--         rows: any[],  -->
<!--         columns: any[],  -->
<!--         leftMargin: number,  -->
<!--         baseWidth: number,  -->
<!--         firstRowY: number,  -->
<!--         rowHeight: number,  -->
<!--         rowFontSize: number -->
<!--     ) { -->
<!--         doc.setFont('helvetica', 'normal'); -->
<!--         doc.setFontSize(rowFontSize); -->

<!--         rows.forEach((row, rowIndex) => { -->
<!--             let columnStart = leftMargin; -->
<!--             columns.forEach(column => { -->
<!--                 const columnEnd = columnStart + column.width * baseWidth; -->
<!--                 const columnCenter = (columnStart + columnEnd) / 2; -->
<!--                 const cellText = row[column.name]; -->
<!--                 const textWidth = doc.getTextWidth(cellText); -->

<!--                 doc.text(cellText, columnCenter - textWidth / 2, firstRowY + rowIndex * rowHeight - 5); -->

<!--                 columnStart = columnEnd; -->
<!--             }); -->
<!--         }); -->
<!--     } -->


<!--     function drawTotalRow( -->
<!--         doc: jsPDF,  -->
<!--         rows: any[],  -->
<!--         columns: any[],  -->
<!--         leftMargin: number,  -->
<!--         baseWidth: number,  -->
<!--         bottomY: number,  -->
<!--         rowFontSize: number -->
<!--     ) { -->
<!--         const totalQuantities = rows.reduce((acc, row) => acc + parseInt(row['QUANTITIES']), 0); -->
<!--         const totalPrices = rows.reduce((acc, row) => acc + parseInt(row['TOTAL']), 0); -->

<!--         doc.setFont('helvetica', 'bold'); -->
<!--         doc.setFontSize(rowFontSize); -->

<!--         const totalRowY = bottomY - 5; -->
<!--         const firstColumnWidth = columns[0].width * baseWidth; -->
<!--         const totalColumnCenter = leftMargin + firstColumnWidth / 2; -->
<!--         const totalTextWidth = doc.getTextWidth('TOTAL'); -->
<!--         doc.text('TOTAL', totalColumnCenter - totalTextWidth / 2, totalRowY); -->

<!--         let columnStart = leftMargin + firstColumnWidth + columns[1].width * baseWidth + columns[2].width * baseWidth; -->
<!--         columns.slice(3).forEach((column, colIndex) => { -->
<!--             const columnEnd = columnStart + column.width * baseWidth; -->
<!--             const columnCenter = (columnStart + columnEnd) / 2; -->
<!--             const cellText = colIndex === 0 ? totalQuantities.toString() : (colIndex === 2 ? totalPrices.toString() : ''); -->
<!--             const textWidth = doc.getTextWidth(cellText); -->

<!--             doc.text(cellText, columnCenter - textWidth / 2, totalRowY); -->

<!--             columnStart = columnEnd; -->
<!--         }); -->
<!--     } -->



<!--     function drawPayToAndFromSections( -->
<!--       doc: jsPDF, -->
<!--       leftMargin: number, -->
<!--       fromY: number, -->
<!--       payToY: number, -->
<!--       pageWidth: number, -->
<!--       labelSpacing: number, -->
<!--       lineSpacing: number = 5, // Line spacing within sections -->
<!--       sectionSpacing: number = 10 // Spacing between "FROM" and "PAY TO" sections -->
<!--     ) { -->
<!--       const labelWidth = doc.getTextWidth('PAY TO:'); -->
<!--       const addressWidth = doc.getTextWidth('Avery Davis123 Anywhere St., Any City123 456 7890'); -->

<!--       const fromLines = [ -->
<!--         { label: 'FROM:', address: 'Really Great Company' }, -->
<!--         { label: '', address: '123 Main St., Anytown USA' }, -->
<!--         { label: '', address: '12345' } -->
<!--       ]; -->

<!--       const payToLines = [ -->
<!--         { label: 'PAY TO:', address: 'Avery Davis' }, -->
<!--         { label: '', address: '123 Anywhere St., Any City' }, -->
<!--         { label: '', address: '123 456 7890' } -->
<!--       ]; -->

<!--       doc.setFont('helvetica', 'normal'); -->
<!--       doc.setFontSize(10); -->

<!--       let currentY = fromY; -->
<!--       fromLines.forEach(({ label, address }) => { -->
<!--         doc.text(label, leftMargin, currentY); -->
<!--         doc.text(address, pageWidth - leftMargin - addressWidth - labelSpacing, currentY); -->
<!--         currentY += lineSpacing; // Adjust the line spacing as needed -->
<!--       }); -->

<!--       currentY += sectionSpacing; // Add spacing between the sections -->

<!--       payToLines.forEach(({ label, address }) => { -->
<!--         doc.text(label, leftMargin, currentY); -->
<!--         doc.text(address, pageWidth - leftMargin - addressWidth - labelSpacing, currentY); -->
<!--         currentY += lineSpacing; -->
<!--       }); -->
<!--     } -->



<!--     function drawInvoiceHeader( -->
<!--       doc: jsPDF, -->
<!--       invoiceNumber: string, -->
<!--       date: string, -->
<!--       pageWidth: number, -->
<!--       leftMargin: number, -->
<!--       topMargin: number, -->
<!--       headerFontSize: number, -->
<!--       invoiceNumberFontSize: number, -->
<!--       dateFontSize: number -->
<!--     ) { -->
<!--       const maxWidth = pageWidth - leftMargin; -->
<!--       const maxHeight = doc.internal.pageSize.getHeight(); -->

<!--       doc.setFont('helvetica', 'bold'); -->
<!--       doc.setFontSize(headerFontSize); -->
<!--       const headerText = 'INVOICE'; -->
<!--       const headerWidth = doc.getTextWidth(headerText); -->
<!--       const headerX = pageWidth - leftMargin - headerWidth; -->
<!--       const headerY = topMargin; -->

<!--       if (headerX >= 0 && headerX <= maxWidth && headerY >= 0 && headerY <= maxHeight) { -->
<!--         doc.text(headerText, headerX, headerY); // Position "INVOICE" header -->
<!--       } -->

<!--       doc.setFontSize(invoiceNumberFontSize); -->
<!--       const invoiceNumberText = `#${invoiceNumber}`; -->
<!--       const invoiceNumberWidth = doc.getTextWidth(invoiceNumberText); -->
<!--       const invoiceNumberX = pageWidth - leftMargin - invoiceNumberWidth; -->
<!--       const invoiceNumberY = headerY + invoiceNumberFontSize + 5; // Position invoice number below "INVOICE" -->

<!--       if (invoiceNumberX >= 0 && invoiceNumberX <= maxWidth && invoiceNumberY >= 0 && invoiceNumberY <= maxHeight) { -->
<!--         doc.text(invoiceNumberText, invoiceNumberX, invoiceNumberY); -->
<!--       } -->

<!--       doc.setFontSize(dateFontSize); -->
<!--       const dateWidth = doc.getTextWidth(date); -->
<!--       const dateX = pageWidth - leftMargin - dateWidth; -->
<!--       const dateY = invoiceNumberY + dateFontSize + 5; // Position date below invoice number -->

<!--       if (dateX >= 0 && dateX <= maxWidth && dateY >= 0 && dateY <= maxHeight) { -->
<!--         doc.text(date, dateX, dateY); -->
<!--       } -->
<!--     } -->




<!--     function drawNoteSection( -->
<!--         doc: jsPDF, -->
<!--         pageWidth: number, -->
<!--         noteY: number, // New parameter to control vertical position -->
<!--         noteFontSize: number, -->
<!--         noteText: string, -->
<!--         noteLineSpacing: number = 2 -->
<!--     ) { -->
<!--         // Split the note text into lines that fit within the page width -->
<!--         const maxTextWidth = pageWidth - 20;    // Let's give some padding from both sides, minus 20 is manually set  -->
<!--                                                 // that's just the padding of the text, think of the css padding -->
<!--         const noteLines = doc.splitTextToSize(noteText, maxTextWidth); -->

<!--         doc.setFont('helvetica', 'normal'); -->
<!--         doc.setFontSize(noteFontSize); -->

<!--         let currentY = noteY; -->

<!--         // Calculate the text width for the widest line -->
<!--         const widestLineWidth = noteLines.reduce((maxWidth, line) => { -->
<!--             const lineWidth = doc.getTextWidth(line); -->
<!--             return Math.max(maxWidth, lineWidth); -->
<!--         }, 0); -->

<!--         // Determine the left margin to center the widest line -->
<!--         const margin = (pageWidth - widestLineWidth) / 2; -->

<!--         // Draw each line of text centered based on the calculated margin -->
<!--         noteLines.forEach((line) => { -->
<!--             const textWidth = doc.getTextWidth(line); -->
<!--             const noteX = (pageWidth - textWidth) / 2; // Center each line with respect to the page width -->
<!--             doc.text(line, noteX, currentY); -->
<!--             currentY += noteFontSize + noteLineSpacing; -->
<!--         }); -->
<!--     } -->





<!--     function generateInvoice(columns: any[], rows: any[]) { -->
<!--         const doc = new jsPDF(); -->

<!--         // Table's section -->
<!--         const baseWidth = 10; -->
<!--         const totalTableWidth = columns.reduce((acc, col) => acc + col.width * baseWidth, 0); -->
<!--         const pageWidth = doc.internal.pageSize.getWidth(); -->
<!--         const pageHeight = doc.internal.pageSize.getHeight(); -->

<!--         const leftMargin = (pageWidth - totalTableWidth) / 2; -->
<!--         const rightMargin = leftMargin + totalTableWidth; -->
<!--         const columnPositions = columns.map((column, index) => leftMargin + columns.slice(0, index).reduce((a, b) => a + b.width * baseWidth, 0)); -->
<!--         const columnWidths = columns.map(column => column.width * baseWidth); -->

<!--         const tableHeaderY = 105; -->
<!--         const subTableHeaderY = tableHeaderY + 10; -->
<!--         const firstRowY = subTableHeaderY + 10; -->
<!--         const rowHeight = 10; -->
<!--         const rowBottomY = firstRowY + rows.length * rowHeight; -->

<!--         const tableHeaderFontSize = Math.floor(rowHeight * 0.7); -->
<!--         const rowFontSize = Math.floor(rowHeight * 0.6); -->


<!--         drawTableLines( -->
<!--             doc,  -->
<!--             leftMargin,  -->
<!--             rightMargin,  -->
<!--             tableHeaderY,  -->
<!--             subTableHeaderY,  -->
<!--             firstRowY,  -->
<!--             rowBottomY,  -->
<!--             rowHeight,  -->
<!--             columnPositions); -->

<!--         const tableBottomY = firstRowY + rows.length * rowHeight; -->

<!--         drawTableHeader(doc, columns, leftMargin, baseWidth, subTableHeaderY, tableHeaderFontSize); -->
<!--         drawTableRows(doc, rows, columns, leftMargin, baseWidth, firstRowY, rowHeight, rowFontSize); -->
<!--         drawTotalRow(doc, rows, columns, leftMargin, baseWidth, rowBottomY, rowFontSize); -->


<!--         // From and To section -->
<!--         const fromY = 40; // Adjust this value to position the whole section of "FROM" and "PAY TO" -->
<!--         const payToY = 60; // Adjust this value to position the "PAY TO" section, but actually no effect -->
<!--         const labelSpacing = 110; // spacing between HEADER and their value -->
<!--         const lineSpacing = 6; // Adjust line spacing within VALUE of PAY TO or VALUE of FROM -->
<!--         const sectionSpacing = 15; // Adjust spacing between "FROM" and "PAY TO" sections -->

<!--         drawPayToAndFromSections(doc, leftMargin, fromY, payToY, pageWidth, labelSpacing, lineSpacing, sectionSpacing); -->



<!--         // Invoice Header Section -->
<!--         const headerFontSize = 20; -->
<!--         const invoiceNumberFontSize = 12; -->
<!--         const dateFontSize = 10; -->
<!--         const headerTopMargin = 40; // Adjust this value to position the header section vertically -->
<!--         const invoiceNumber = 'SDF00023' -->
<!--         const invoiceDate = 'July 1, 2024' -->

<!--         drawInvoiceHeader( -->
<!--             doc, -->
<!--             invoiceNumber, -->
<!--             invoiceDate, -->
<!--             pageWidth, -->
<!--             leftMargin, -->
<!--             headerTopMargin, -->
<!--             headerFontSize, -->
<!--             invoiceNumberFontSize, -->
<!--             dateFontSize -->
<!--         ); -->

<!--   -->

<!--         const noteText = 'This is a note section. \nYou can write multiple lines of text here.'; -->
<!--         const noteFontSize = 10; -->
<!--         const noteLineSpacing = 2; -->
<!--         const noteTopSpacing = 20; // parameter to control spacing between table and note -->

<!--         const noteY = tableBottomY + noteTopSpacing; // Position the note below the table with spacing -->

<!--         drawNoteSection(doc, pageWidth, noteY, noteFontSize, noteText, noteLineSpacing); -->



<!--         doc.save('invoice.pdf'); -->
<!--     } -->




<!--     // set up the standard template for invoice table -->
<!--     const columns = [ -->
<!--         { name: 'PRODUCT REF', width: 3, offset: 0 }, -->
<!--         { name: 'DESCRIPTION', width: 5 }, -->
<!--         { name: 'H.S.CODE', width: 2 }, -->
<!--         { name: 'QUANTITIES', width: 3 }, -->
<!--         { name: 'UNIT PRICE', width: 3 }, -->
<!--         { name: 'TOTAL', width: 2 } -->
<!--     ]; -->

<!--     // Later pass the data into the function, the result parameter -->
<!--     // append the unit to quantities, handle in frontend input, and just pass that here as value -->
<!--     // export const results: any[] = []; -->

<!--     const rows = [ -->
<!--         { 'PRODUCT REF': 'PR001', 'DESCRIPTION': 'Product 1', 'H.S.CODE': '1234', 'QUANTITIES': '10', 'UNIT PRICE': '50', 'TOTAL': '500' }, -->
<!--         { 'PRODUCT REF': 'PR002', 'DESCRIPTION': 'Product 2', 'H.S.CODE': '5678', 'QUANTITIES': '20', 'UNIT PRICE': '30', 'TOTAL': '600' }, -->
<!--         { 'PRODUCT REF': 'PR003', 'DESCRIPTION': 'Product 3', 'H.S.CODE': '9101', 'QUANTITIES': '15', 'UNIT PRICE': '40', 'TOTAL': '600' }, -->
<!--         { 'PRODUCT REF': 'PR004', 'DESCRIPTION': 'Product 4', 'H.S.CODE': '1121', 'QUANTITIES': '5', 'UNIT PRICE': '100', 'TOTAL': '500' }, -->
<!--         { 'PRODUCT REF': 'PR005', 'DESCRIPTION': 'Product 5', 'H.S.CODE': '3141', 'QUANTITIES': '8', 'UNIT PRICE': '70', 'TOTAL': '560' }, -->
<!--         { 'PRODUCT REF': 'PR006', 'DESCRIPTION': 'Product 6', 'H.S.CODE': '3149', 'QUANTITIES': '7', 'UNIT PRICE': '41', 'TOTAL': '290' }, -->
<!--     ]; -->



<!-- </script> -->

<!-- <button class='btn' on:click={() => generateInvoice(columns, rows)}>Invoice</button> -->




