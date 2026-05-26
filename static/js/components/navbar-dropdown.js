/**
 * Navbar Dropdown Component
 * Handles profile dropdown and mobile slide-in menu
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

    setupProfileDropdown() {
        const profileButton = document.getElementById('profile-menu-button');
        const profileMenu = document.getElementById('profile-menu');

        if (!profileButton || !profileMenu) return;

        profileButton.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleProfileDropdown(profileButton, profileMenu);
        });

        document.addEventListener('click', (e) => {
            if (!profileMenu.classList.contains('hidden') &&
                !profileButton.contains(e.target) &&
                !profileMenu.contains(e.target)) {
                this.closeProfileDropdown(profileButton, profileMenu);
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !profileMenu.classList.contains('hidden')) {
                this.closeProfileDropdown(profileButton, profileMenu);
                profileButton.focus();
            }
        });

        this.setupMenuItemNavigation(profileMenu);
    }

    setupMobileMenu() {
        this.mobileMenuButton = document.getElementById('mobile-menu-button');
        this.mobileMenu = document.getElementById('mobile-menu');
        this.mobileBackdrop = document.getElementById('mobile-menu-backdrop');
        this.menuIconClosed = document.getElementById('menu-icon-closed');
        this.menuIconOpen = document.getElementById('menu-icon-open');

        if (!this.mobileMenuButton || !this.mobileMenu) return;

        this.mobileMenuButton.addEventListener('click', () => {
            this.toggleMobileMenu();
        });

        if (this.mobileBackdrop) {
            this.mobileBackdrop.addEventListener('click', () => {
                this.closeMobileMenu();
            });
        }

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.mobileMenu.classList.contains('active')) {
                this.closeMobileMenu();
                this.mobileMenuButton.focus();
            }
        });

        let startX = 0;
        let currentX = 0;
        let isDragging = false;

        this.mobileMenu.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            isDragging = true;
        }, { passive: true });

        this.mobileMenu.addEventListener('touchmove', (e) => {
            if (!isDragging) return;
            currentX = e.touches[0].clientX;
            const diff = currentX - startX;
            if (diff > 0) {
                this.mobileMenu.style.transform = `translateX(${diff}px)`;
            }
        }, { passive: true });

        this.mobileMenu.addEventListener('touchend', () => {
            if (!isDragging) return;
            isDragging = false;
            const diff = currentX - startX;
            if (diff > 80) {
                this.closeMobileMenu();
            } else {
                this.mobileMenu.style.transform = '';
            }
            startX = 0;
            currentX = 0;
        }, { passive: true });
    }

    setupKeyboardNavigation() {
        const profileMenu = document.getElementById('profile-menu');
        if (profileMenu) {
            profileMenu.addEventListener('keydown', (e) => {
                this.handleMenuKeyNavigation(e, profileMenu);
            });
        }
    }

    toggleMobileMenu() {
        if (this.mobileMenu.classList.contains('active')) {
            this.closeMobileMenu();
        } else {
            this.openMobileMenu();
        }
    }

    openMobileMenu() {
        this.mobileMenu.classList.remove('hidden');
        if (this.mobileBackdrop) this.mobileBackdrop.classList.remove('hidden');

        requestAnimationFrame(() => {
            this.mobileMenu.classList.add('active');
            if (this.mobileBackdrop) this.mobileBackdrop.classList.add('active');
        });

        this.mobileMenuButton.setAttribute('aria-expanded', 'true');
        if (this.menuIconClosed && this.menuIconOpen) {
            this.menuIconClosed.classList.add('hidden');
            this.menuIconOpen.classList.remove('hidden');
        }

        document.body.style.overflow = 'hidden';

        const firstLink = this.mobileMenu.querySelector('.mobile-nav-item');
        if (firstLink) firstLink.focus();
    }

    closeMobileMenu() {
        this.mobileMenu.classList.remove('active');
        this.mobileMenu.style.transform = '';
        if (this.mobileBackdrop) this.mobileBackdrop.classList.remove('active');

        this.mobileMenuButton.setAttribute('aria-expanded', 'false');
        if (this.menuIconClosed && this.menuIconOpen) {
            this.menuIconClosed.classList.remove('hidden');
            this.menuIconOpen.classList.add('hidden');
        }

        document.body.style.overflow = '';

        setTimeout(() => {
            this.mobileMenu.classList.add('hidden');
            if (this.mobileBackdrop) this.mobileBackdrop.classList.add('hidden');
        }, 300);
    }

    toggleProfileDropdown(button, menu) {
        if (menu.classList.contains('hidden')) {
            this.openProfileDropdown(button, menu);
        } else {
            this.closeProfileDropdown(button, menu);
        }
    }

    openProfileDropdown(button, menu) {
        menu.classList.remove('hidden');
        button.setAttribute('aria-expanded', 'true');
        const firstMenuItem = menu.querySelector('[role="menuitem"]');
        if (firstMenuItem) firstMenuItem.focus();
    }

    closeProfileDropdown(button, menu) {
        menu.classList.add('hidden');
        button.setAttribute('aria-expanded', 'false');
    }

    setupMenuItemNavigation(menu) {
        const menuItems = menu.querySelectorAll('[role="menuitem"]');

        menuItems.forEach((item, index) => {
            item.setAttribute('tabindex', '-1');
            item.addEventListener('keydown', (e) => {
                switch (e.key) {
                    case 'ArrowDown':
                        e.preventDefault();
                        menuItems[(index + 1) % menuItems.length].focus();
                        break;
                    case 'ArrowUp':
                        e.preventDefault();
                        menuItems[(index - 1 + menuItems.length) % menuItems.length].focus();
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

    handleMenuKeyNavigation(e, menu) {
        const menuItems = menu.querySelectorAll('[role="menuitem"]');
        const currentIndex = Array.from(menuItems).indexOf(document.activeElement);

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                menuItems[(currentIndex + 1) % menuItems.length].focus();
                break;
            case 'ArrowUp':
                e.preventDefault();
                menuItems[(currentIndex - 1 + menuItems.length) % menuItems.length].focus();
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

document.addEventListener('DOMContentLoaded', () => {
    new NavbarDropdown();
});
