function adjustAllParentsPrecisely(selector) {
    document.querySelectorAll(selector).forEach(parent => {
        let maxBottom = 0;

        const parentRect = parent.getBoundingClientRect();
        const parentScrollTop = parent.scrollTop;

        Array.from(parent.children).forEach(child => {
            const childRect = child.getBoundingClientRect();
            const bottom = childRect.bottom - parentRect.top + parentScrollTop;

            if (bottom > maxBottom) {
                maxBottom = bottom;
            }
        });

        parent.style.height = `${Math.ceil(maxBottom)}px`;
    });
}

window.addEventListener("load", () => {
    adjustAllParentsPrecisely(".div, .background, .container, .body");
});

window.addEventListener("resize", () => {
    adjustAllParentsPrecisely(".div, .background, .container, .body");
});