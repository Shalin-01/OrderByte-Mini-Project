document.addEventListener('DOMContentLoaded', function() {
    // Initialize search functionality
    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');
    const filterButtons = document.querySelectorAll('.filter-btn');
    
    // Current filters
    let currentCategory = 'all';
    let showInStockOnly = false;
    let allItems = []; // All menu items for search
    
    // Fetch menu items
    fetchMenuItems();
    
    // Event listeners for search and filters
    searchInput.addEventListener('input', updateResults);
    
    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Special handling for "In Stock Only" filter
            if (button.dataset.category === 'in-stock') {
                button.classList.toggle('active');
                showInStockOnly = button.classList.contains('active');
            } else {
                // Normal category filters
                filterButtons.forEach(btn => {
                    if (btn.dataset.category !== 'in-stock') {
                        btn.classList.remove('active');
                    }
                });
                button.classList.add('active');
                currentCategory = button.dataset.category;
            }
            updateResults();
        });
    });
    
    // Initialize dropdown menu
    window.toggleDropdown = function() {
        const dropdownMenu = document.getElementById('dropdownMenu');
        dropdownMenu.style.display = dropdownMenu.style.display === 'block' ? 'none' : 'block';
    };
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(event) {
        const avatar = document.querySelector('.avatar');
        const dropdown = document.getElementById('dropdownMenu');
        
        if (dropdown && dropdown.style.display === 'block' && 
            event.target !== avatar && 
            !dropdown.contains(event.target)) {
            dropdown.style.display = 'none';
        }
    });
    
   
    
    // Process menu items for search
    function processMenuItems(items) {
        // Convert items object to array with IDs
        allItems = Object.entries(items).map(([id, item]) => ({
            id,
            ...item
        }));
        
        // Update search results
        updateResults();
    }
    
    async function fetchMenuItems() {
        try {
          // Show loading indicator
          searchResults.innerHTML = '<div class="loading">Loading menu items...</div>'
      
          // Get today's date in YYYYMMDD format
          const today = new Date().toISOString().slice(0, 10).replace(/-/g, "")
      
          // Fetch the published menu for today
          const response = await fetch(`/api/published-menus/${today}`)
      
          if (!response.ok) {
            throw new Error("No menu published for today")
          }
      
          const data = await response.json()
      
          if (!data || !data.items || Object.keys(data.items).length === 0) {
            throw new Error("No menu items available")
          }
      
          // Process menu items - make sure to check in_stock status
          processMenuItems(data.items)
        } catch (error) {
          console.error("Error fetching menu:", error)
          searchResults.innerHTML = '<div class="no-results">No menu available for today. Please check back later.</div>'
        }
      }
      
    // Update the updateResults function to correctly handle stock status and display buttons like the home page
function updateResults() {
    const searchTerm = searchInput.value.toLowerCase()
    searchResults.innerHTML = "" // Clear previous results
  
    if (allItems.length === 0) {
      searchResults.innerHTML = '<div class="no-results">No menu items available</div>'
      return
    }
  
    // Filter items based on search term, category, and stock status
    const filteredItems = allItems.filter((item) => {
      // Filter by search term
      const nameMatch = item.name.toLowerCase().includes(searchTerm)
      const descriptionMatch = item.description && item.description.toLowerCase().includes(searchTerm)
  
      // Filter by category
      const categoryMatch = currentCategory === "all" || item.category.toLowerCase() === currentCategory.toLowerCase()
  
      // Filter by stock status
      const stockMatch = !showInStockOnly || (item.in_stock && item.stock_count > 0)
  
      return (nameMatch || descriptionMatch) && categoryMatch && stockMatch
    })
  
    if (filteredItems.length === 0) {
      searchResults.innerHTML = '<div class="no-results">No items match your search</div>'
      return
    }
  
    // Render filtered items
    filteredItems.forEach((item) => {
      const foodCard = document.createElement("div")
      foodCard.className = "food-card"
      foodCard.dataset.itemId = item.id
  
      // Add out-of-stock class if needed
      if (!item.in_stock || item.stock_count <= 0) {
        foodCard.classList.add("out-of-stock")
      }
  
      const originalPrice = item.price
      const discount = item.discount || 0
      const discountedPrice = originalPrice * (1 - discount / 100)
  
      // Check if item is actually in stock (both flag and count)
      const isInStock = item.in_stock && item.stock_count > 0
  
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
            isInStock
              ? `<div style="margin-bottom: 10px; font-size: 0.9em; color: #38a169;">
                  ${item.stock_count} left in stock
                </div>`
              : `<div style="margin-bottom: 10px; font-size: 0.9em; color: #e53e3e;">
                  Out of stock
                </div>`
          }
          <div style="display: flex; flex-direction: column; gap: 8px;">
            ${
              isInStock
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
  
      searchResults.appendChild(foodCard)
    })
  }
  
      
    
    // Add to cart function
    window.addToCart = function(itemId) {
        fetch(`/api/cart/add`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                item_id: itemId,
                quantity: 1
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Show success message
                showNotification(`Item added to cart!`);
            } else {
                showNotification(`Error: ${data.error}`, true);
            }
        })
        .catch(error => {
            console.error('Error adding to cart:', error);
            showNotification('Failed to add item to cart. Please try again.', true);
        });
    };
    
    // Show notification
    function showNotification(message, isError = false) {
        // Create notification element if it doesn't exist
        let notification = document.getElementById('notification');
        if (!notification) {
            notification = document.createElement('div');
            notification.id = 'notification';
            notification.style.position = 'fixed';
            notification.style.bottom = '20px';
            notification.style.right = '20px';
            notification.style.padding = '10px 20px';
            notification.style.borderRadius = '4px';
            notification.style.color = 'white';
            notification.style.zIndex = '1000';
            notification.style.transition = 'opacity 0.3s ease-in-out';
            document.body.appendChild(notification);
        }
        
        // Set notification style based on type
        notification.style.backgroundColor = isError ? '#ff6b6b' : '#4CAF50';
        notification.textContent = message;
        notification.style.opacity = '1';
        
        // Hide notification after 3 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
        }, 3000);
    }
    
    // Show item details in a modal
    window.showItemDetails = function(itemId) {
        fetch(`/api/menu-items/${itemId}`)
        .then(response => response.json())
        .then(item => {
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
                                    ${item.discount ? 
                                        `<span class="discounted-price">₹${(item.price - (item.price * item.discount / 100)).toFixed(2)}</span> 
                                         <span class="original-price">₹${item.price.toFixed(2)}</span>
                                         <span class="discount-badge">${item.discount}% OFF</span>` 
                                        : 
                                        `<span class="regular-price">₹${item.price.toFixed(2)}</span>`
                                    }
                                </div>
                                <div class="item-description">
                                    <h3>Description</h3>
                                    <p>${item.description}</p>
                                </div>
                                ${item.in_stock ? 
                                    `<div class="item-stock">
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
                                    : 
                                    `<div class="item-stock out">
                                        <span class="out-of-stock-badge">OUT OF STOCK</span>
                                    </div>`
                                }
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button class="cancel-btn" onclick="closeItemDetails()">Cancel</button>
                            <button class="add-to-cart-btn" ${!item.in_stock ? 'disabled' : ''} onclick="addToCartWithQuantity('${item.id}')">
                                Add to Cart
                            </button>
                        </div>
                    </div>
                </div>
            `;
            
            // Add modal to the page
            document.body.insertAdjacentHTML('beforeend', modalHTML);
            
            // Add styles for the modal
            const modalStyles = document.createElement('style');
            modalStyles.id = 'modalStyles';
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
                .item-stock h3,
                .item-quantity h3 {
                    font-size: 1rem;
                    margin-bottom: 5px;
                    color: #555;
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
            `;
            
            document.head.appendChild(modalStyles);
        })
        .catch(error => {
            console.error('Error fetching item details:', error);
            showNotification('Failed to load item details. Please try again.', true);
        });
    };
    
    // Close item details modal
    window.closeItemDetails = function() {
        const modal = document.getElementById('itemDetailsModal');
        if (modal) {
            modal.remove();
        }
        
        const modalStyles = document.getElementById('modalStyles');
        if (modalStyles) {
            modalStyles.remove();
        }
    };
    
    // Update quantity in the details modal
    window.updateQuantity = function(action, maxQuantity = 100) {
        const quantityElement = document.getElementById('itemQuantity');
        let currentQuantity = parseInt(quantityElement.textContent);
        
        if (action === 'increase' && currentQuantity < maxQuantity) {
            quantityElement.textContent = currentQuantity + 1;
        } else if (action === 'decrease' && currentQuantity > 1) {
            quantityElement.textContent = currentQuantity - 1;
        }
    };
    
    // Add to cart with quantity from details modal
    window.addToCartWithQuantity = function(itemId) {
        const quantityElement = document.getElementById('itemQuantity');
        const quantity = parseInt(quantityElement.textContent);
        
        fetch(`/api/cart/add`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                item_id: itemId,
                quantity: quantity
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Close the modal
                closeItemDetails();
                
                // Show success message
                showNotification(`Added ${quantity} item(s) to cart!`);
            } else {
                showNotification(`Error: ${data.error}`, true);
            }
        })
        .catch(error => {
            console.error('Error adding to cart:', error);
            showNotification('Failed to add item to cart. Please try again.', true);
        });
    };
});