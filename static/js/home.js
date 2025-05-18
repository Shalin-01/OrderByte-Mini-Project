document.addEventListener("DOMContentLoaded", () => {
  // Initialize dropdown menu
  function toggleDropdown() {
    const dropdownMenu = document.getElementById("dropdownMenu")
    if (dropdownMenu) {
      dropdownMenu.style.display = dropdownMenu.style.display === "block" ? "none" : "block"
    }
  }

  // Make toggleDropdown available globally
  window.toggleDropdown = toggleDropdown

  // Close dropdown when clicking outside
  document.addEventListener("click", (event) => {
    const avatar = document.getElementById("navAvatar")
    const dropdown = document.getElementById("dropdownMenu")

    if (dropdown && dropdown.style.display === "block" && event.target !== avatar && !dropdown.contains(event.target)) {
      dropdown.style.display = "none"
    }
  })

  // Fetch today's menu
  fetchTodayMenu()

  // Add scroll functionality to all scroll containers
  setupScrollButtons()
})

// Fetch today's menu from the server
async function fetchTodayMenu() {
  const loadingIndicator = document.getElementById("loadingIndicator")
  const noMenuMessage = document.getElementById("noMenuMessage")

  try {
    // Get today's date in YYYYMMDD format
    const today = new Date().toISOString().slice(0, 10).replace(/-/g, "")

    // Show loading indicator
    if (loadingIndicator) {
      loadingIndicator.style.display = "flex"
    }

    // Fetch the published menu for today
    const response = await fetch(`/api/published-menus/${today}`)

    if (!response.ok) {
      throw new Error("No menu published for today")
    }

    const data = await response.json()

    if (!data || !data.items || Object.keys(data.items).length === 0) {
      throw new Error("No menu items available")
    }

    // Process menu items by category
    processMenuItems(data.items)

    // Hide loading indicator
    if (loadingIndicator) {
      loadingIndicator.style.display = "none"
    }
  } catch (error) {
    console.error("Error fetching menu:", error)

    // Hide loading indicator
    if (loadingIndicator) {
      loadingIndicator.style.display = "none"
    }

    // Show no menu message
    if (noMenuMessage) {
      noMenuMessage.style.display = "block"
    }
  }
}

// Process menu items and organize by category
function processMenuItems(items) {
  // Convert items object to array with IDs
  const itemsArray = Object.entries(items).map(([id, item]) => ({
    id,
    ...item,
  }))

  // Group items by category
  const itemsByCategory = {}
  const specialItems = []

  itemsArray.forEach((item) => {
    // Check for special items regardless of stock status
    if (item.special) {
      specialItems.push(item)
    }

    // Add to category regardless of stock status
    if (!itemsByCategory[item.category]) {
      itemsByCategory[item.category] = []
    }

    itemsByCategory[item.category].push(item)
  })

  // Clear main content first
  const mainContent = document.querySelector(".main-content")
  if (!mainContent) return

  // Keep only loading indicator and no menu message
  const loadingIndicator = document.getElementById("loadingIndicator")
  const noMenuMessage = document.getElementById("noMenuMessage")
  mainContent.innerHTML = ""
  if (loadingIndicator) mainContent.appendChild(loadingIndicator)
  if (noMenuMessage) mainContent.appendChild(noMenuMessage)

  // Create a special section for Today's Specials
  if (specialItems.length > 0) {
    const specialSection = document.createElement("section")
    specialSection.className = "category-section"
    specialSection.id = "specialSection"

    const specialTitle = document.createElement("h2")
    specialTitle.className = "category-title"
    specialTitle.innerHTML = `
            <a class="category-link">
                Today's Specials
                <span class="arrow">→</span>
            </a>
        `

    const scrollContainer = createScrollContainer("specialGrid", specialItems)

    specialSection.appendChild(specialTitle)
    specialSection.appendChild(scrollContainer)

    // Add to main content
    mainContent.appendChild(specialSection)
  }

  // Define the order of categories
  const categoryOrder = ["Breakfast", "Lunch", "Curry", "Desserts", "Drinks"]

  // Populate each category section in the defined order
  categoryOrder.forEach((category) => {
    if (itemsByCategory[category] && itemsByCategory[category].length > 0) {
      const section = document.createElement("section")
      section.className = "category-section"
      section.id = category.toLowerCase().replace(/[^a-z0-9]+/g, "") + "Section"

      const title = document.createElement("h2")
      title.className = "category-title"
      title.innerHTML = `
                <a class="category-link">
                    ${category}
                    <span class="arrow">→</span>
                </a>
            `

      section.appendChild(title)

      const scrollContainer = createScrollContainer(
        category.toLowerCase().replace(/[^a-z0-9]+/g, "") + "Grid",
        itemsByCategory[category],
      )
      section.appendChild(scrollContainer)

      // Add to main content
      mainContent.appendChild(section)
    }
  })

  // Setup scroll buttons after populating content
  setupScrollButtons()
}

// Create a scroll container with items
function createScrollContainer(gridId, items) {
  const scrollContainer = document.createElement("div")
  scrollContainer.className = "scroll-container"

  const scrollButtons = document.createElement("div")
  scrollButtons.className = "scroll-buttons"
  scrollButtons.innerHTML = `
        <button class="scroll-btn left">←</button>
        <button class="scroll-btn right">→</button>
    `

  const foodGrid = document.createElement("div")
  foodGrid.className = "food-grid"
  foodGrid.id = gridId

  // Add items to grid
  items.forEach((item) => {
    const foodCard = createFoodCard(item)
    foodGrid.appendChild(foodCard)
  })

  scrollContainer.appendChild(scrollButtons)
  scrollContainer.appendChild(foodGrid)

  return scrollContainer
}

// Create a food card element
function createFoodCard(item) {
  const foodCard = document.createElement("div")
  foodCard.className = "food-card"
  foodCard.dataset.itemId = item.id

  // Add out-of-stock class if needed
  if (!item.in_stock || item.stock_count <= 0) {
    foodCard.classList.add("out-of-stock")
  }

  // Calculate discounted price if applicable
  const originalPrice = item.price
  const discountedPrice = item.discount ? originalPrice - (originalPrice * item.discount) / 100 : originalPrice

  foodCard.innerHTML = `
          <img src="${item.image_url}" alt="${item.name}" class="food-image">
          <div class="food-info">
              <h3 class="food-name">${item.name}</h3>
              <div class="food-price">
                  ${
                    item.discount
                      ? `<span>₹${discountedPrice.toFixed(2)}</span> 
                       <span style="text-decoration: line-through; color: #999; font-size: 0.9em;">₹${originalPrice.toFixed(2)}</span>
                       <span style="color: #e53e3e; font-size: 0.8em; margin-left: 5px;">${item.discount}% OFF</span>`
                      : `₹${originalPrice.toFixed(2)}`
                  }
              </div>
              ${
                item.in_stock && item.stock_count > 0
                  ? `<div style="margin-bottom: 10px; font-size: 0.9em; color: #38a169;">
                      ${item.stock_count} left in stock
                  </div>`
                  : `<div style="margin-bottom: 10px; font-size: 0.9em; color: #e53e3e;">
                      Out of stock
                  </div>`
              }
              <div style="display: flex; flex-direction: column; gap: 8px;">
                  ${
                    item.in_stock && item.stock_count > 0
                      ? `<button class="add-to-cart" onclick="addToCart('${item.id}')">
                          Add to Cart
                      </button>`
                      : `<div class="out-of-stock-label">
                          Out of Stock
                      </div>`
                  }
                  <button class="details-btn" style="width: 100%;" onclick="showItemDetails('${item.id}')">
                      Details
                  </button>
              </div>
          </div>
      `

  return foodCard
}

// Setup scroll buttons for all scroll containers
function setupScrollButtons() {
  const scrollContainers = document.querySelectorAll(".scroll-container")

  scrollContainers.forEach((container) => {
    const leftBtn = container.querySelector(".scroll-btn.left")
    const rightBtn = container.querySelector(".scroll-btn.right")
    const grid = container.querySelector(".food-grid")

    if (leftBtn && rightBtn && grid) {
      // Initial check for scroll buttons visibility
      updateScrollButtonsVisibility(grid, leftBtn, rightBtn)

      // Add click event listeners
      leftBtn.addEventListener("click", () => {
        grid.scrollBy({ left: -300, behavior: "smooth" })
      })

      rightBtn.addEventListener("click", () => {
        grid.scrollBy({ left: 300, behavior: "smooth" })
      })

      // Add scroll event listener to update button visibility
      grid.addEventListener("scroll", () => {
        updateScrollButtonsVisibility(grid, leftBtn, rightBtn)
      })

      // Add resize event listener to update button visibility
      window.addEventListener("resize", () => {
        updateScrollButtonsVisibility(grid, leftBtn, rightBtn)
      })
    }
  })
}

// Helper function to update scroll buttons visibility
function updateScrollButtonsVisibility(grid, leftBtn, rightBtn) {
  // Check if at the start (left edge)
  const isAtStart = grid.scrollLeft <= 0

  // Check if at the end (right edge)
  const isAtEnd = grid.scrollLeft + grid.clientWidth >= grid.scrollWidth - 1 // -1 for rounding errors

  // Update button visibility
  leftBtn.style.display = isAtStart ? "none" : "flex"
  rightBtn.style.display = isAtEnd ? "none" : "flex"
}

// Add item to cart
function addToCart(itemId) {
  // Show loading indicator or disable button to prevent multiple clicks
  const button =
    document.querySelector(`.cart-item[data-item-id="${itemId}"] .add-to-cart`) ||
    document.querySelector(`[data-item-id="${itemId}"] .add-to-cart`)

  if (button) {
    const originalText = button.textContent
    button.textContent = "Added"
    button.disabled = true
  }

  fetch(`/api/cart/add`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      item_id: itemId,
      quantity: 1,
    }),
  })
    .then((response) => {
      if (!response.ok) {
        return response.json().then((data) => {
          throw new Error(data.error || "Failed to add item to cart")
        })
      }
      return response.json()
    })
    .then((data) => {
      if (data.success) {
        // Show success message
        showNotification(`Item added to cart!`)
      } else {
        showNotification(`Error: ${data.error}`, true)
      }
    })
    .catch((error) => {
      console.error("Error adding to cart:", error)
      showNotification(error.message || "Failed to add item to cart. Please try again.", true)
    })
    .finally(() => {
      // Reset button state
      if (button) {
        button.textContent = originalText
        button.disabled = false
      }
    })
}

// Show notification
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

// Show item details in a modal
function showItemDetails(itemId) {
  fetch(`/api/menu-items/${itemId}`)
    .then((response) => response.json())
    .then((item) => {
      // Create modal HTML
      const modalHTML = `
            <div class="modal-overlay" id="itemDetailsModal">
                <div class="modal-content">
                    <span class="close-modal" onclick="closeItemDetails()">&times;</span>
                    <div class="modal-header">
                        <h2>${item.name}</h2>
                    </div>
                    <div class="modal-body">
                        <div class="item-image-container">
                            <img src="${item.image_url}" alt="${item.name}" class="item-detail-image">
                        </div>
                        <div class="item-details">
                            <div class="item-price">
                                ${
                                  item.discount
                                    ? `<span class="discounted-price">₹${(item.price - (item.price * item.discount) / 100).toFixed(2)}</span> 
                                     <span class="original-price">₹${item.price.toFixed(2)}</span>
                                     <span class="discount-badge">${item.discount}% OFF</span>`
                                    : `<span class="regular-price">₹${item.price.toFixed(2)}</span>`
                                }
                            </div>
                            <div class="item-description">
                                <h3>Description</h3>
                                <p>${item.description}</p>
                            </div>
                            ${
                              item.in_stock && item.stock_count > 0
                                ? `<div class="item-stock">
                                    <h3>Availability</h3>
                                    <p>${item.stock_count} left in stock</p>
                                </div>
                                <div class="item-quantity">
                                    <h3>Quantity</h3>
                                    <div class="quantity-selector">
                                        <button onclick="updateQuantity('decrease')">-</button>
                                        <span id="itemQuantity">1</span>
                                        <button onclick="updateQuantity('increase', ${item.stock_count})">+</button>
                                    </div>
                                </div>`
                                : `<div class="item-stock out">
                                    <span class="out-of-stock-badge">OUT OF STOCK</span>
                                </div>`
                            }
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="cancel-btn" onclick="closeItemDetails()">Cancel</button>
                        <button class="add-to-cart-btn" ${!item.in_stock || item.stock_count <= 0 ? "disabled" : ""} onclick="addToCartWithQuantity('${item.id}')">
                            Add to Cart
                        </button>
                    </div>
                </div>
            </div>
        `

      // Add modal to the page
      document.body.insertAdjacentHTML("beforeend", modalHTML)

      // Add styles for the modal
      const modalStyles = document.createElement("style")
      modalStyles.id = "modalStyles"
      modalStyles.textContent = `
            .modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.7);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 1001;
            }
            
            .modal-content {
                background-color: white;
                border-radius: 8px;
                width: 90%;
                max-width: 500px;
                max-height: 90vh;
                overflow-y: auto;
                position: relative;
            }
            
            .close-modal {
                position: absolute;
                top: 10px;
                right: 15px;
                font-size: 24px;
                cursor: pointer;
                color: #666;
            }
            
            .modal-header {
                padding: 15px 20px;
                border-bottom: 1px solid #eee;
            }
            
            .modal-body {
                padding: 20px;
            }
            
            .item-image-container {
                width: 100%;
                height: 250px;
                margin-bottom: 20px;
                border-radius: 8px;
                overflow: hidden;
            }
            
            .item-detail-image {
                width: 100%;
                height: 100%;
                object-fit: cover;
            }
            
            .item-details {
                display: flex;
                flex-direction: column;
                gap: 15px;
            }
            
            .item-price {
                font-size: 1.2rem;
                margin-bottom: 10px;
            }
            
            .discounted-price {
                font-weight: bold;
                color: #000;
            }
            
            .original-price {
                text-decoration: line-through;
                color: #999;
                margin-left: 8px;
                font-size: 0.9rem;
            }
            
            .discount-badge {
                background-color: #e53e3e;
                color: white;
                padding: 2px 6px;
                border-radius: 4px;
                font-size: 0.8rem;
                margin-left: 8px;
            }
            
            .regular-price {
                font-weight: bold;
            }
            
            .item-description h3,
            .item-stock h3 {
                font-size: 1rem;
                margin-bottom: 5px;
                color: #555;
            }
            
            .stock-status {
                margin: 10px 0;
            }
            
            .in-stock-text {
                color: #38a169;
                font-weight: bold;
            }
            
            .out-of-stock-badge {
                background-color: #e53e3e;
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-weight: bold;
            }
            
            .quantity-selector {
                display: flex;
                align-items: center;
                gap: 15px;
                margin-top: 10px;
            }
            
            .quantity-selector button {
                width: 30px;
                height: 30px;
                border-radius: 50%;
                border: 1px solid #ddd;
                background: white;
                font-size: 1.2rem;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
            }
            
            .modal-footer {
                padding: 15px 20px;
                border-top: 1px solid #eee;
                display: flex;
                justify-content: flex-end;
                gap: 10px;
            }
            
            .cancel-btn {
                padding: 8px 15px;
                border: 1px solid #ddd;
                background: white;
                border-radius: 4px;
                cursor: pointer;
            }
            
            .add-to-cart-btn {
                padding: 8px 15px;
                background-color: #303F9F;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            
            .add-to-cart-btn:disabled {
                background-color: #ccc;
                cursor: not-allowed;
            }
        `

      document.head.appendChild(modalStyles)
    })
    .catch((error) => {
      console.error("Error fetching item details:", error)
      showNotification("Failed to load item details. Please try again.", true)
    })
}

// Close item details modal
function closeItemDetails() {
  const modal = document.getElementById("itemDetailsModal")
  if (modal) {
    modal.remove()
  }

  const modalStyles = document.getElementById("modalStyles")
  if (modalStyles) {
    modalStyles.remove()
  }
}

// Update quantity in the details modal
function updateQuantity(action, maxQuantity = 100) {
  const quantityElement = document.getElementById("itemQuantity")
  const currentQuantity = Number.parseInt(quantityElement.textContent)

  if (action === "increase" && currentQuantity < maxQuantity) {
    quantityElement.textContent = currentQuantity + 1
  } else if (action === "decrease" && currentQuantity > 1) {
    quantityElement.textContent = currentQuantity - 1
  }
}

// Add to cart with quantity from details modal
function addToCartWithQuantity(itemId) {
  const quantityElement = document.getElementById("itemQuantity")
  const quantity = Number.parseInt(quantityElement.textContent)

  // Disable button to prevent multiple clicks
  const button = document.querySelector(".add-to-cart-btn")
  if (button) {
    const originalText = button.textContent
    button.textContent = "Adding..."
    button.disabled = true
  }

  fetch(`/api/cart/add`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      item_id: itemId,
      quantity: quantity,
    }),
  })
    .then((response) => {
      if (!response.ok) {
        return response.json().then((data) => {
          throw new Error(data.error || "Failed to add item to cart")
        })
      }
      return response.json()
    })
    .then((data) => {
      if (data.success) {
        // Close the modal
        closeItemDetails()

        // Show success message
        showNotification(`Added ${quantity} item(s) to cart!`)
      } else {
        showNotification(`Error: ${data.error}`, true)
      }
    })
    .catch((error) => {
      console.error("Error adding to cart:", error)
      showNotification(error.message || "Failed to add item to cart. Please try again.", true)
    })
    .finally(() => {
      // Reset button state if modal is still open
      if (button && document.getElementById("itemDetailsModal")) {
        button.textContent = "Add to Cart"
        button.disabled = false
      }
    })
}
