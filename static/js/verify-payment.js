// This script handles payment verification and stock updates

async function verifyPayment(paymentResponse) {
  try {
    // First verify the payment with Razorpay
    const verifyResponse = await fetch("/verify-payment", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(paymentResponse),
    })

    const verifyData = await verifyResponse.json()

    if (verifyData.success) {
      // Payment verified successfully
      showNotification("Payment successful! Your order has been placed.")

      // Now update the stock quantities
      const orderId = verifyData.order_id

      try {
        // Call the update-stock API
        const stockResponse = await fetch("/api/update-stock", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ order_id: orderId }),
        })

        const stockData = await stockResponse.json()

        if (!stockData.success) {
          console.error("Error updating stock:", stockData.error)
          // We don't show this error to the user since the payment was successful
        }
      } catch (stockError) {
        console.error("Error updating stock:", stockError)
        // We don't show this error to the user since the payment was successful
      }

      // Redirect to order confirmation page
      setTimeout(() => {
        window.location.href = `/order-confirmation/${orderId}`
      }, 1500)
    } else {
      showNotification("Payment verification failed. Please contact support.", true)
    }
  } catch (error) {
    console.error("Error verifying payment:", error)
    showNotification("Error verifying payment. Please contact support.", true)
  }
}

// Function to show notification
function showNotification(message, isError = false) {
  // Create notification element if it doesn't exist
  let notification = document.getElementById("notification")
  if (!notification) {
    notification = document.createElement("div")
    notification.id = "notification"
    notification.style.position = "fixed"
    notification.style.bottom = "20px"
    notification.style.right = "20px"
    notification.style.padding = "10px 20px"
    notification.style.borderRadius = "4px"
    notification.style.color = "white"
    notification.style.zIndex = "1000"
    notification.style.transition = "opacity 0.3s ease-in-out"
    document.body.appendChild(notification)
  }

  // Set notification style based on type
  notification.style.backgroundColor = isError ? "#ff6b6b" : "#4CAF50"
  notification.textContent = message
  notification.style.opacity = "1"

  // Hide notification after 3 seconds
  setTimeout(() => {
    notification.style.opacity = "0"
  }, 3000)
}
