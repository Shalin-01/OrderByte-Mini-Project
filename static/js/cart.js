document.addEventListener("DOMContentLoaded", () => {
  // Get DOM elements
  const cartItemsContainer = document.getElementById("cartItems")
  const subtotalElement = document.getElementById("subtotal")
  const totalElement = document.getElementById("total")
  const proceedToPayBtn = document.getElementById("proceedToPayBtn")
  const continueShoppingBtn = document.getElementById("continueShopping")

  // Fetch cart items from server
  fetchCartItems()

  // Continue shopping button event listener
  if (continueShoppingBtn) {
    continueShoppingBtn.addEventListener("click", () => {
      window.location.href = "/home"
    })
  }

  // Proceed to pay button event listener
  if (proceedToPayBtn) {
    proceedToPayBtn.addEventListener("click", () => {
      // Check if cart has items before proceeding
      const cartItems = document.querySelectorAll(".cart-item")
      if (cartItems.length > 0) {
        // Initialize Razorpay payment
        initializeRazorpayPayment()
      } else {
        alert("Your cart is empty. Add some items first!")
      }
    })
  }

  // Function to fetch cart items from server
  function fetchCartItems() {
    // Show loading indicator
    cartItemsContainer.innerHTML = '<div class="loading">Loading your cart...</div>'

    fetch("/get-cart-items")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to fetch cart items")
        }
        return response.json()
      })
      .then((data) => {
        if (data.success && data.cart) {
          // Check if cart has items for current date
          if (data.cart.items && Object.keys(data.cart.items).length > 0) {
            renderCartItems(data.cart.items)
            updateCartSummary(data.cart.total)

            // Store cart in localStorage for checkout page
            saveCartToLocalStorage(data.cart.items)
          } else {
            showEmptyCart()
          }
        } else {
          showEmptyCart()
        }
      })
      .catch((error) => {
        console.error("Error fetching cart items:", error)
        showEmptyCart()
        showNotification("Error loading cart items. Please try again.", true)
      })
  }

  // Function to save cart to localStorage
  function saveCartToLocalStorage(items) {
    const today = new Date().toISOString().slice(0, 10)

    const cartItems = Object.values(items).map((item) => ({
      id: item.id,
      name: item.name,
      price: item.price,
      quantity: item.quantity,
      image: item.image_url,
      date: today, // Add current date to track when item was added
    }))

    localStorage.setItem("cart", JSON.stringify(cartItems))
  }

  // Function to show empty cart message
  function showEmptyCart() {
    cartItemsContainer.innerHTML = `
      <div class="empty-cart">
        <h2>Your cart is empty</h2>
        <p>Looks like you haven't added any items to your cart yet.</p>
        <button id="emptyCartShopBtn" class="btn-primary" style="margin-top: 18px;border-radius: 40px;width: 200px;height: 23px;border: none;">Browse Menu</button>
      </div>
    `
    updateCartSummary(0)

    // Clear localStorage cart
    localStorage.setItem("cart", JSON.stringify([]))

    // Add event listener to the browse menu button
    const emptyCartShopBtn = document.getElementById("emptyCartShopBtn")
    if (emptyCartShopBtn) {
      emptyCartShopBtn.addEventListener("click", () => {
        window.location.href = "/home"
      })
    }
  }

  // Function to update cart summary
  function updateCartSummary(total) {
    const subtotal = total
    // You can add tax calculation or shipping costs here if needed
    const finalTotal = subtotal

    subtotalElement.textContent = `₹${subtotal.toFixed(2)}`
    totalElement.textContent = `₹${finalTotal.toFixed(2)}`
  }

  // Function to add event listeners to quantity buttons
  function addQuantityButtonListeners() {
    // Decrease quantity buttons
    document.querySelectorAll(".decrease-btn").forEach((button) => {
      button.addEventListener("click", function () {
        const itemId = this.dataset.itemId
        updateItemQuantity(itemId, -1)
      })
    })

    // Increase quantity buttons
    document.querySelectorAll(".increase-btn").forEach((button) => {
      button.addEventListener("click", function () {
        const itemId = this.dataset.itemId
        updateItemQuantity(itemId, 1)
      })
    })
  }

  // Function to add event listeners to remove buttons
  function addRemoveButtonListeners() {
    document.querySelectorAll(".remove-btn").forEach((button) => {
      button.addEventListener("click", function () {
        const itemId = this.dataset.itemId
        removeItemFromCart(itemId)
      })
    })
  }

  // Update the renderCartItems function to properly display discounted prices
  function renderCartItems(items) {
    cartItemsContainer.innerHTML = ""

    if (!items || Object.keys(items).length === 0) {
      showEmptyCart()
      return
    }

    // Convert items object to array for easier handling
    const itemsArray = Object.values(items)

    itemsArray.forEach((item) => {
      const itemElement = document.createElement("div")
      itemElement.className = "cart-item"
      itemElement.dataset.itemId = item.id

      // Check if decrease button should be disabled (quantity = 1)
      const decreaseDisabled = item.quantity <= 1 ? "disabled" : ""

      // Check if increase button should be disabled (quantity = stock_count)
      const increaseDisabled = item.quantity >= item.stock_count ? "disabled" : ""

      // Prepare price display with discount information if applicable
      let priceDisplay = `₹${item.price.toFixed(2)}`
      if (item.discount && item.discount > 0) {
        priceDisplay = `
        <span style="text-decoration: line-through; color: #999; font-size: 0.9em;">₹${item.original_price.toFixed(2)}</span>
        <span>₹${item.price.toFixed(2)}</span>
        <span style="color: #e53e3e; font-size: 0.8em; margin-left: 5px;">${item.discount}% OFF</span>
      `
      }

      itemElement.innerHTML = `
      <div class="item-image">
        <img src="${item.image_url}" alt="${item.name}">
      </div>
      <div class="item-details">
        <h3>${item.name}</h3>
        <p class="item-price">${priceDisplay}</p>
      </div>
      <div class="item-quantity">
        <button class="quantity-btn decrease-btn" data-item-id="${item.id}" ${decreaseDisabled}>-</button>
        <span class="quantity">${item.quantity}</span>
        <button class="quantity-btn increase-btn" data-item-id="${item.id}" ${increaseDisabled}>+</button>
      </div>
      <div class="item-total">₹${(item.price * item.quantity).toFixed(2)}</div>
      <button class="remove-btn" data-item-id="${item.id}">&times;</button>
    `

      cartItemsContainer.appendChild(itemElement)
    })

    // Add event listeners to the buttons
    addQuantityButtonListeners()
    addRemoveButtonListeners()
  }

  // Function to update item quantity
  function updateItemQuantity(itemId, change) {
    // Disable buttons to prevent multiple clicks
    const buttons = document.querySelectorAll(`.cart-item[data-item-id="${itemId}"] .quantity-btn`)
    buttons.forEach((btn) => (btn.disabled = true))

    fetch("/update-cart-item", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        item_id: itemId,
        quantity_change: change,
      }),
    })
      .then((response) => {
        if (!response.ok) {
          return response.json().then((data) => {
            throw new Error(data.error || "Failed to update cart")
          })
        }
        return response.json()
      })
      .then((data) => {
        if (data.success) {
          // Update the UI without reloading the page
          const itemElement = document.querySelector(`.cart-item[data-item-id="${itemId}"]`)
          if (itemElement) {
            const quantityElement = itemElement.querySelector(".quantity")
            const itemTotalElement = itemElement.querySelector(".item-total")
            const decreaseBtn = itemElement.querySelector(".decrease-btn")
            const increaseBtn = itemElement.querySelector(".increase-btn")

            const newQuantity = data.item.quantity
            const itemPrice = data.item.price
            const maxStock = data.item.stock_count || 0

            // If quantity becomes 0, remove the item
            if (newQuantity <= 0) {
              itemElement.remove()
            } else {
              quantityElement.textContent = newQuantity
              itemTotalElement.textContent = `₹${(itemPrice * newQuantity).toFixed(2)}`

              // Disable decrease button if quantity is 1
              if (newQuantity <= 1) {
                decreaseBtn.disabled = true
              } else {
                decreaseBtn.disabled = false
              }

              // Disable increase button if quantity equals stock count
              if (newQuantity >= maxStock) {
                increaseBtn.disabled = true
              } else {
                increaseBtn.disabled = false
              }
            }
          }

          // Update cart summary
          updateCartSummary(data.cart.total)

          // Update localStorage cart
          saveCartToLocalStorage(data.cart.items || {})

          // Show empty cart message if cart is empty
          if (Object.keys(data.cart.items || {}).length === 0) {
            showEmptyCart()
          }

          // Show success notification
          showNotification("Cart updated successfully")
        } else {
          console.error("Failed to update cart:", data.message)
          showNotification(data.message || "Failed to update cart", true)
        }
      })
      .catch((error) => {
        console.error("Error updating cart:", error)
        showNotification(error.message || "Error updating cart. Please try again.", true)
      })
      .finally(() => {
        // Re-enable buttons that still exist in the DOM
        const existingButtons = document.querySelectorAll(`.cart-item[data-item-id="${itemId}"] .quantity-btn`)
        existingButtons.forEach((btn) => {
          // We don't re-enable here because we handle enabling/disabling in the success callback
        })
      })
  }

  // Function to remove item from cart
  function removeItemFromCart(itemId) {
    // Use update-cart-item with a large negative quantity to remove the item
    updateItemQuantity(itemId, -1000)
  }

  // Function to initialize Razorpay payment
  function initializeRazorpayPayment() {
    // Get the total amount from the DOM
    const totalAmount = Number.parseFloat(totalElement.textContent.replace("₹", "")) * 100 // Convert to paise

    // Fetch order details from server
    fetch("/create-razorpay-order", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        amount: totalAmount,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success && data.order_id) {
          // Initialize Razorpay checkout
          const options = {
            key: data.razorpay_key_id, // Get from server
            amount: totalAmount,
            currency: "INR",
            name: "OrderByte",
            description: "Food Order Payment",
            order_id: data.order_id,
            handler: (response) => {
              // Handle successful payment
              verifyPayment(response)
            },
            prefill: {
              name: data.user_name || "",
              email: data.user_email || "",
              contact: data.user_phone || "",
            },
            theme: {
              color: "#303F9F",
            },
          }

          const rzp = new Razorpay(options)
          rzp.open()

          // Handle payment failure
          rzp.on("payment.failed", (response) => {
            showNotification("Payment failed. Please try again.", true)
            console.error("Payment failed:", response.error)
          })
        } else {
          showNotification("Could not create payment order. Please try again.", true)
        }
      })
      .catch((error) => {
        console.error("Error creating Razorpay order:", error)
        showNotification("Error processing payment. Please try again.", true)
      })
  }

  // Function to verify payment with server
  function verifyPayment(paymentResponse) {
    fetch("/verify-payment", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(paymentResponse),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          // Payment verified successfully
          showNotification("Payment successful! Your order has been placed.")
          // Redirect to order confirmation page
          setTimeout(() => {
            window.location.href = `/order-confirmation/${data.order_id}`
          }, 1500)
        } else {
          showNotification("Payment verification failed. Please contact support.", true)
        }
      })
      .catch((error) => {
        console.error("Error verifying payment:", error)
        showNotification("Error verifying payment. Please contact support.", true)
      })
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
})

function toggleDropdown() {
  const dropdown = document.getElementById("dropdownMenu")
  dropdown.style.display = dropdown.style.display === "block" ? "none" : "block"
}

// Hide dropdown when clicking outside
document.addEventListener("click", (event) => {
  const dropdown = document.getElementById("dropdownMenu")
  if (dropdown && !event.target.closest(".avatar-container")) {
    dropdown.style.display = "none"
  }
})

window.onpageshow = (event) => {
  // If page is loaded from cache (like using back button)
  if (event.persisted) {
    // Make an AJAX request to check authentication
    fetch("/check_auth")
      .then((response) => response.json())
      .then((data) => {
        if (!data.authenticated) {
          window.location.href = "/index"
        }
      })
  }
  // Add this to your checkout.js or create a new JS file

document.addEventListener('DOMContentLoaded', function() {
    // Check for pending orders when the checkout page loads
    checkForPendingOrders();
    
    // Function to check for pending orders
    function checkForPendingOrders() {
        fetch('/api/get-pending-orders')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.pending_orders && data.pending_orders.length > 0) {
                    // Show notification about pending orders
                    showPendingOrderNotification(data.pending_orders);
                }
            })
            .catch(error => {
                console.error('Error checking pending orders:', error);
            });
    }
    
    // Function to show notification about pending orders
    function showPendingOrderNotification(pendingOrders) {
        const mostRecentOrder = pendingOrders[0];
        
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'pending-order-notification';
        notification.innerHTML = `
            <div class="notification-content">
                <h4>You have a pending order</h4>
                <p>You started an order but didn't complete payment.</p>
                <p>Amount: ₹${mostRecentOrder.amount}</p>
                <p>Created: ${formatDate(mostRecentOrder.created_at)}</p>
                <button class="btn btn-primary" id="continue-order-btn">Continue with this order</button>
                <button class="btn btn-outline-secondary" id="new-order-btn">Create new order</button>
                <button class="btn btn-close" id="close-notification-btn">×</button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Style the notification
        const style = document.createElement('style');
        style.textContent = `
            .pending-order-notification {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                max-width: 350px;
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                padding: 16px;
                animation: slide-in 0.3s ease-out;
            }
            
            .notification-content h4 {
                margin-top: 0;
                margin-bottom: 10px;
                color: #333;
            }
            
            .notification-content p {
                margin-bottom: 8px;
                color: #666;
            }
            
            .notification-content button {
                margin-top: 10px;
                margin-right: 5px;
            }
            
            #close-notification-btn {
                position: absolute;
                top: 8px;
                right: 8px;
                padding: 0;
                width: 24px;
                height: 24px;
                font-size: 16px;
                line-height: 1;
            }
            
            @keyframes slide-in {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        
        document.head.appendChild(style);
        
        // Add event listeners
        document.getElementById('continue-order-btn').addEventListener('click', function() {
            // Continue with existing order
            continueWithPendingOrder(mostRecentOrder);
            notification.remove();
        });
        
        document.getElementById('new-order-btn').addEventListener('click', function() {
            // Just close the notification and proceed with new order
            notification.remove();
        });
        
        document.getElementById('close-notification-btn').addEventListener('click', function() {
            notification.remove();
        });
    }
    
    // Function to continue with a pending order
    function continueWithPendingOrder(order) {
        // Use the existing Razorpay order ID
        const razorpayOrderId = order.order_id;
        
        // Get user details (assuming you have them available)
        const userName = order.user_name || '';
        const userEmail = order.user_email || '';
        const userPhone = order.user_phone || '';
        
        // Assuming you have a function to create the Razorpay payment form
        // similar to what you would do in a new order
        initializeRazorpayCheckout(
            razorpayOrderId, 
            Math.round(order.amount * 100), // Convert to paise
            userName,
            userEmail,
            userPhone
        );
    }
    
    // Format date for display
    function formatDate(isoDate) {
        if (!isoDate) return 'Unknown date';
        
        const date = new Date(isoDate);
        return date.toLocaleString();
    }
    
    // Initialize Razorpay Checkout
    // This is just an example - adapt to your existing Razorpay integration
    function initializeRazorpayCheckout(orderId, amount, name, email, phone) {
        // Fetch the Razorpay key ID from your server or use it directly if safe
        fetch('/api/get-razorpay-key')
            .then(response => response.json())
            .then(data => {
                const options = {
                    key: data.razorpay_key_id,
                    amount: amount,
                    currency: "INR",
                    name: "Your Restaurant Name",
                    description: "Order Payment",
                    order_id: orderId,
                    handler: function (response) {
                        // Handle successful payment
                        verifyPayment(response);
                    },
                    prefill: {
                        name: name,
                        email: email,
                        contact: phone
                    },
                    notes: {
                        address: "Customer Address"
                    },
                    theme: {
                        color: "#3399cc"
                    }
                };
                
                const rzp1 = new Razorpay(options);
                rzp1.open();
            })
            .catch(error => {
                console.error("Error initializing Razorpay:", error);
            });
    }
    
    // Function to verify payment with your server
    function verifyPayment(response) {
        fetch('/verify-payment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(response)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Payment successful
                window.location.href = '/order-confirmation/' + data.order_id;
            } else {
                // Payment failed
                alert('Payment verification failed: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Payment verification error:', error);
            alert('An error occurred during payment verification.');
        });
    }
});
}
