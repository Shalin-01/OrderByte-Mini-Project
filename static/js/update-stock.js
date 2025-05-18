// Import the Firebase Admin SDK
import { db } from "@/firebaseAdmin"

// API route to update stock quantities after an order is placed
export async function POST(request) {
  try {
    const data = await request.json()
    const { orderId } = data

    if (!orderId) {
      return Response.json({ success: false, error: "Order ID is required" }, { status: 400 })
    }

    // Fetch order details from Firebase
    const orderRef = db.reference(`orders/${orderId}`)
    const order = await orderRef.get()

    if (!order) {
      return Response.json({ success: false, error: "Order not found" }, { status: 404 })
    }

    // Get today's date in YYYYMMDD format
    const today = new Date().toISOString().slice(0, 10).replace(/-/g, "")

    // Get the published menu for today
    const publishedMenuRef = db.reference(`published_menus/${today}`)
    const publishedMenu = await publishedMenuRef.get()

    if (!publishedMenu || !publishedMenu.items) {
      return Response.json({ success: false, error: "Menu not found" }, { status: 404 })
    }

    // Update stock for each item in the order
    const updates = {}
    let stockUpdated = false

    if (order.items) {
      for (const [itemId, item] of Object.entries(order.items)) {
        if (publishedMenu.items[itemId]) {
          const menuItem = publishedMenu.items[itemId]
          const quantity = item.quantity || 1

          // Calculate new stock count
          const currentStock = menuItem.stock_count || 0
          const newStock = Math.max(0, currentStock - quantity)

          // Update stock count
          updates[`items/${itemId}/stock_count`] = newStock

          // Update in_stock status if stock becomes 0
          if (newStock === 0) {
            updates[`items/${itemId}/in_stock`] = false
          }

          stockUpdated = true
        }
      }
    }

    // Apply updates to the published menu
    if (stockUpdated) {
      await publishedMenuRef.update(updates)

      // Also update the default menu items for future reference
      const defaultMenuRef = db.reference("menu_items")
      for (const [itemId, item] of Object.entries(order.items)) {
        const defaultItemRef = defaultMenuRef.child(itemId)
        const defaultItem = await defaultItemRef.get()

        if (defaultItem) {
          const quantity = item.quantity || 1
          const currentStock = defaultItem.stock_count || 0
          const newStock = Math.max(0, currentStock - quantity)

          await defaultItemRef.update({
            stock_count: newStock,
            in_stock: newStock > 0,
          })
        }
      }
    }

    // Update order status to indicate stock has been updated
    await orderRef.update({ stock_updated: true })

    return Response.json({ success: true, message: "Stock updated successfully" })
  } catch (error) {
    console.error("Error updating stock:", error)
    return Response.json({ success: false, error: error.message }, { status: 500 })
  }
}
