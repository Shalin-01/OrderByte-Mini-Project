// Next.js version updates - route.js
import { NextResponse } from "next/server"
import { PDFDocument, StandardFonts, rgb } from "pdf-lib" // Note: added rgb import
import { db } from "@/lib/db"
import { ref, update } from "firebase/database"

export async function POST(req) {
  try {
    const { orderId } = await req.json()

    if (!orderId) {
      return new NextResponse("Order ID is required", { status: 400 })
    }

    const order_ref = ref(db, "orders/" + orderId)
    const orderSnapshot = await (await fetch(`/api/get-order?orderId=${orderId}`)).json()
    const order = orderSnapshot.order

    if (!order) {
      return new NextResponse("Order not found", { status: 404 })
    }

    const pdfDoc = await PDFDocument.create()
    const page = pdfDoc.addPage()

    const font = await pdfDoc.embedFont(StandardFonts.Helvetica)
    const boldFont = await pdfDoc.embedFont(StandardFonts.HelveticaBold)

    // Header
    page.drawText("Invoice", {
      x: 50,
      y: 750,
      font: boldFont,
      size: 36,
    })

    // Order Status - Add this new section
    const orderStatus = order.status || "pending"
    let statusColor = rgb(0, 0, 0) // Default black

    // Set color based on status
    if (orderStatus.toLowerCase() === "cancelled") {
      statusColor = rgb(0.8, 0, 0) // Red for cancelled
    } else if (orderStatus.toLowerCase() === "approved") {
      statusColor = rgb(0, 0.6, 0) // Green for approved
    } else if (orderStatus.toLowerCase() === "paid") {
      statusColor = rgb(0, 0.4, 0.8) // Blue for paid
    }

    // Draw status with appropriate color
    page.drawText(`Status: ${orderStatus.toUpperCase()}`, {
      x: 400,
      y: 750,
      font: boldFont,
      size: 18,
      color: statusColor,
    })

    // Draw watermark for cancelled orders
    if (orderStatus.toLowerCase() === "cancelled") {
      page.drawText("CANCELLED", {
        x: 150,
        y: 400,
        font: boldFont,
        size: 72,
        color: rgb(0.8, 0, 0, 0.3), // Red with transparency
        rotate: {
          type: "degrees",
          angle: -45,
        },
      })
    }

    // Invoice Details
    page.drawText(`Invoice Number: ${orderId}`, { x: 50, y: 700, font, size: 12 })

    // Add payment ID if available
    if (order.payment_id) {
      page.drawText(`Payment ID: ${order.payment_id}`, { x: 50, y: 660, font, size: 12 })
      // Adjust the y-coordinate of subsequent elements
      page.drawText(`Date: ${new Date().toLocaleDateString()}`, { x: 50, y: 640, font, size: 12 })

      // Customer Details - adjust y-coordinates
      page.drawText("Bill to:", { x: 50, y: 600, font: boldFont, size: 12 })
      page.drawText(order.customerName || "Unknown Customer", { x: 50, y: 580, font, size: 12 })
      page.drawText(order.customerEmail || "No Email", { x: 50, y: 560, font, size: 12 })

      // Adjust table y-coordinate
      tableY = 510
    } else {
      // Keep original y-coordinates if no payment ID
      page.drawText(`Date: ${new Date().toLocaleDateString()}`, { x: 50, y: 680, font, size: 12 })
    }

    // Customer Details
    page.drawText("Bill to:", { x: 50, y: 640, font: boldFont, size: 12 })
    page.drawText(order.customerName || "Unknown Customer", { x: 50, y: 620, font, size: 12 })
    page.drawText(order.customerEmail || "No Email", { x: 50, y: 600, font, size: 12 })

    // Table Header
    const tableX = 50
    let tableY = 550
    const columnWidths = [200, 100, 50, 100] // Adjusted column widths
    const columnHeaders = ["Item", "Price", "Quantity", "Total"]

    page.drawText(columnHeaders[0], { x: tableX, y: tableY, font: boldFont, size: 12 })
    page.drawText(columnHeaders[1], { x: tableX + columnWidths[0], y: tableY, font: boldFont, size: 12 })
    page.drawText(columnHeaders[2], {
      x: tableX + columnWidths[0] + columnWidths[1],
      y: tableY,
      font: boldFont,
      size: 12,
    })
    page.drawText(columnHeaders[3], {
      x: tableX + columnWidths[0] + columnWidths[1] + columnWidths[2],
      y: tableY,
      font: boldFont,
      size: 12,
    })

    tableY -= 20

    // Table Rows
    let subtotal = 0
    const tableRows = []

    if (order.items) {
      for (const [itemId, item] of Object.entries(order.items)) {
        const originalPrice = item.price || 0
        const discount = item.discount || 0
        const discountedPrice = discount > 0 ? originalPrice - (originalPrice * discount) / 100 : originalPrice
        const quantity = item.quantity || 1
        const total = discountedPrice * quantity

        // Include discount information in the table
        let priceDisplay = `₹${discountedPrice.toFixed(2)}`
        if (discount > 0) {
          priceDisplay = `₹${discountedPrice.toFixed(2)} (${discount}% off ₹${originalPrice.toFixed(2)})`
        }

        tableRows.push([item.name || "Unknown Item", priceDisplay, quantity, `₹${total.toFixed(2)}`])

        subtotal += total
      }
    }

    tableRows.forEach((row) => {
      page.drawText(row[0], { x: tableX, y: tableY, font, size: 12 })
      page.drawText(row[1], { x: tableX + columnWidths[0], y: tableY, font, size: 12 })
      page.drawText(row[2].toString(), { x: tableX + columnWidths[0] + columnWidths[1], y: tableY, font, size: 12 })
      page.drawText(row[3], {
        x: tableX + columnWidths[0] + columnWidths[1] + columnWidths[2],
        y: tableY,
        font,
        size: 12,
      })
      tableY -= 20
    })

    // Subtotal, Tax, and Total
    let finalY = tableY - 20
    page.drawText("Subtotal:", { x: 50, y: finalY, font: boldFont, size: 12, align: "right" })
    page.drawText(`₹${subtotal.toFixed(2)}`, 170, finalY, { align: "right" })

    finalY -= 20
    page.drawText("Tax (0%):", { x: 50, y: finalY, font: boldFont, size: 12, align: "right" })
    page.drawText("₹0.00", 170, finalY, { align: "right" })

    finalY -= 20
    page.drawText("Total:", { x: 50, y: finalY + 25, font: boldFont, size: 14, align: "right" })

    // Always use the calculated subtotal to ensure discounts are reflected
    page.drawText(`₹${subtotal.toFixed(2)}`, 170, finalY + 25, { align: "right" })
    // Update the order amount if it doesn't match the calculated total
    if (order.amount !== subtotal) {
      update(order_ref, { amount: subtotal })
    }

    // Add a note for cancelled orders
    if (orderStatus.toLowerCase() === "cancelled") {
      finalY -= 40
      page.drawText("Note: This order has been cancelled. No payment is due.", {
        x: 50,
        y: finalY,
        font: boldFont,
        size: 12,
        color: rgb(0.8, 0, 0),
      })
    }

    const pdfBytes = await pdfDoc.save()

    return new NextResponse(pdfBytes, {
      status: 200,
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `attachment; filename="invoice-${orderId}.pdf"`,
      },
    })
  } catch (error) {
    console.error("Error generating invoice:", error)
    return new NextResponse("Internal Server Error", { status: 500 })
  }
}
