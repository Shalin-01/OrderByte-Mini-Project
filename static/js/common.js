// Common JavaScript functions for OrderByte

// Toggle dropdown menu
function toggleDropdown() {
  const dropdown = document.getElementById("dropdownMenu")
  dropdown.style.display = dropdown.style.display === "block" ? "none" : "block"
}

// Close dropdown when clicking outside
document.addEventListener("click", (event) => {
  const dropdown = document.getElementById("dropdownMenu")
  if (!event.target.closest(".avatar-container")) {
    dropdown.style.display = "none"
  }
})

// Check authentication on page load
window.onpageshow = (event) => {
  // If page is loaded from cache (like using back button)
  if (event.persisted) {
    // Make an AJAX request to check authentication
    fetch("/check_auth")
      .then((response) => response.json())
      .then((data) => {
        if (!data.authenticated) {
          window.location.href = "/signin"
        } else {
          // Update avatar if needed
          updateUserAvatar()
        }
      })
  } else {
    // Update avatar on normal page load
    updateUserAvatar()
  }
}

// Function to update user avatar
function updateUserAvatar() {
  fetch("/api/user/current")
    .then((response) => response.json())
    .then((data) => {
      if (data.success && data.user) {
        const avatarImg = document.getElementById("navAvatar")
        if (avatarImg && data.user.profile_picture) {
          avatarImg.src = data.user.profile_picture
        }
      }
    })
    .catch((error) => console.error("Error fetching user data:", error))
}
