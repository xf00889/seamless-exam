/**
 * Navbar Dropdown Component
 * Handles profile dropdown and mobile menu functionality
 */

class NavbarDropdown {
    constructor() {
        this.init();
    }

    init() {
        this.setupProfileDropdown();
        this.setupMobileMenu();
        this.setupKeyboardNavigation();
    }

    /**
     * Setup profile dropdown functionality
     */
    setupProfileDropdown() {
        const profileButton = document.getElementById('profile-menu-button');
        const profileMenu = document.getElementById('profile-menu');
        
        if (!profileButton || !profileMenu) return;

        // Toggle dropdown on button click
        profileButton.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleProfileDropdown(profileButton, profileMenu);
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!profileMenu.classList.contains('hidden') && 
                !profileButton.contains(e.target) && 
                !profileMenu.contains(e.target)) {
                this.closeProfileDropdown(profileButton, profileMenu);
            }
        });
        
        // Close dropdown on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !profileMenu.classList.contains('hidden')) {
                this.closeProfileDropdown(profileButton, profileMenu);
                profileButton.focus();
            }
        });

        // Handle menu item keyboard navigation
        this.setupMenuItemNavigation(profileMenu);
    }

    /**
     * Setup mobile menu functionality
     */
    setupMobileMenu() {
        const mobileMenuButton = document.getElementById('mobile-menu-button');
        const mobileMenu = document.getElementById('mobile-menu');
        const menuIconClosed = document.getElementById('menu-icon-closed');
        const menuIconOpen = document.getElementById('menu-icon-open');
        
        if (!mobileMenuButton || !mobileMenu) return;

        mobileMenuButton.addEventListener('click', () => {
            this.toggleMobileMenu(
                mobileMenuButton, 
                mobileMenu, 
                menuIconClosed, 
                menuIconOpen
            );
        });

        // Close mobile menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!mobileMenu.classList.contains('hidden') && 
                !mobileMenuButton.contains(e.target) && 
                !mobileMenu.contains(e.target)) {
                this.closeMobileMenu(
                    mobileMenuButton, 
                    mobileMenu, 
                    menuIconClosed, 
                    menuIconOpen
                );
            }
        });

        // Close mobile menu on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !mobileMenu.classList.contains('hidden')) {
                this.closeMobileMenu(
                    mobileMenuButton, 
                    mobileMenu, 
                    menuIconClosed, 
                    menuIconOpen
                );
                mobileMenuButton.focus();
            }
        });
    }

    /**
     * Setup keyboard navigation for accessibility
     */
    setupKeyboardNavigation() {
        // Handle arrow key navigation in dropdowns
        const profileMenu = document.getElementById('profile-menu');
        if (profileMenu) {
            profileMenu.addEventListener('keydown', (e) => {
                this.handleMenuKeyNavigation(e, profileMenu);
            });
        }
    }

    /**
     * Toggle profile dropdown
     * @param {HTMLButtonElement} button - Profile button
     * @param {HTMLElement} menu - Profile menu
     */
    toggleProfileDropdown(button, menu) {
        const isHidden = menu.classList.contains('hidden');
        
        if (isHidden) {
            this.openProfileDropdown(button, menu);
        } else {
            this.closeProfileDropdown(button, menu);
        }
    }

    /**
     * Open profile dropdown
     * @param {HTMLButtonElement} button - Profile button
     * @param {HTMLElement} menu - Profile menu
     */
    openProfileDropdown(button, menu) {
        menu.classList.remove('hidden');
        button.setAttribute('aria-expanded', 'true');
        
        // Focus first menu item for accessibility
        const firstMenuItem = menu.querySelector('[role="menuitem"]');
        if (firstMenuItem) {
            firstMenuItem.focus();
        }
    }

    /**
     * Close profile dropdown
     * @param {HTMLButtonElement} button - Profile button
     * @param {HTMLElement} menu - Profile menu
     */
    closeProfileDropdown(button, menu) {
        menu.classList.add('hidden');
        button.setAttribute('aria-expanded', 'false');
    }

    /**
     * Toggle mobile menu
     * @param {HTMLButtonElement} button - Mobile menu button
     * @param {HTMLElement} menu - Mobile menu
     * @param {HTMLElement} iconClosed - Closed menu icon
     * @param {HTMLElement} iconOpen - Open menu icon
     */
    toggleMobileMenu(button, menu, iconClosed, iconOpen) {
        const isHidden = menu.classList.contains('hidden');
        
        if (isHidden) {
            this.openMobileMenu(button, menu, iconClosed, iconOpen);
        } else {
            this.closeMobileMenu(button, menu, iconClosed, iconOpen);
        }
    }

    /**
     * Open mobile menu
     * @param {HTMLButtonElement} button - Mobile menu button
     * @param {HTMLElement} menu - Mobile menu
     * @param {HTMLElement} iconClosed - Closed menu icon
     * @param {HTMLElement} iconOpen - Open menu icon
     */
    openMobileMenu(button, menu, iconClosed, iconOpen) {
        menu.classList.remove('hidden');
        button.setAttribute('aria-expanded', 'true');
        
        if (iconClosed && iconOpen) {
            iconClosed.classList.add('hidden');
            iconOpen.classList.remove('hidden');
        }
    }

    /**
     * Close mobile menu
     * @param {HTMLButtonElement} button - Mobile menu button
     * @param {HTMLElement} menu - Mobile menu
     * @param {HTMLElement} iconClosed - Closed menu icon
     * @param {HTMLElement} iconOpen - Open menu icon
     */
    closeMobileMenu(button, menu, iconClosed, iconOpen) {
        menu.classList.add('hidden');
        button.setAttribute('aria-expanded', 'false');
        
        if (iconClosed && iconOpen) {
            iconClosed.classList.remove('hidden');
            iconOpen.classList.add('hidden');
        }
    }

    /**
     * Setup menu item navigation for accessibility
     * @param {HTMLElement} menu - Menu element
     */
    setupMenuItemNavigation(menu) {
        const menuItems = menu.querySelectorAll('[role="menuitem"]');
        
        menuItems.forEach((item, index) => {
            item.setAttribute('tabindex', '-1');
            
            item.addEventListener('keydown', (e) => {
                switch (e.key) {
                    case 'ArrowDown':
                        e.preventDefault();
                        const nextIndex = (index + 1) % menuItems.length;
                        menuItems[nextIndex].focus();
                        break;
                    case 'ArrowUp':
                        e.preventDefault();
                        const prevIndex = (index - 1 + menuItems.length) % menuItems.length;
                        menuItems[prevIndex].focus();
                        break;
                    case 'Home':
                        e.preventDefault();
                        menuItems[0].focus();
                        break;
                    case 'End':
                        e.preventDefault();
                        menuItems[menuItems.length - 1].focus();
                        break;
                }
            });
        });
    }

    /**
     * Handle keyboard navigation in menus
     * @param {KeyboardEvent} e - Keyboard event
     * @param {HTMLElement} menu - Menu element
     */
    handleMenuKeyNavigation(e, menu) {
        const menuItems = menu.querySelectorAll('[role="menuitem"]');
        const currentIndex = Array.from(menuItems).indexOf(document.activeElement);
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                if (currentIndex < menuItems.length - 1) {
                    menuItems[currentIndex + 1].focus();
                } else {
                    menuItems[0].focus();
                }
                break;
            case 'ArrowUp':
                e.preventDefault();
                if (currentIndex > 0) {
                    menuItems[currentIndex - 1].focus();
                } else {
                    menuItems[menuItems.length - 1].focus();
                }
                break;
            case 'Home':
                e.preventDefault();
                menuItems[0].focus();
                break;
            case 'End':
                e.preventDefault();
                menuItems[menuItems.length - 1].focus();
                break;
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new NavbarDropdown();
});