document.addEventListener('DOMContentLoaded', function() {
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) {
            return parts.pop().split(';').shift();
        }
        return '';
    }

    const csrfToken = getCookie('csrftoken');

    document.querySelectorAll('.buy-button').forEach(function(button) {
        button.addEventListener('click', function() {
            var itemId = this.dataset.itemId;
            fetch(`/buy/${itemId}/`)
                .then(response => response.json())
                .then(session => window.location.href = session.session_url);
        });
    });

    document.querySelectorAll('.add-order-button').forEach(function(button) {
        button.addEventListener('click', async function() {
            const itemId = this.dataset.itemId;

            const quantityInput = document.getElementById('quantity-' + itemId);
            const rawQuantity = quantityInput ? parseInt(quantityInput.value, 10) : 1;
            const maxStock = quantityInput ? parseInt(quantityInput.max, 10) : NaN;

            if (Number.isNaN(rawQuantity) || rawQuantity < 1) {
                alert('Quantity must be greater than or equal to 1');
                return;
            }

            const quantity = Number.isNaN(maxStock) ? rawQuantity : Math.min(rawQuantity, maxStock);

            const response = await fetch(`/cart/add/${itemId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({
                    quantity: quantity
                })
            });
            const data = await response.json();
            if (!response.ok) {
                alert(data.error || 'Failed to add item to cart');
                return;
            }

            if (typeof data.total_quantity !== 'undefined') {
                document.getElementById('cart-count').textContent = data.total_quantity;
            }
        });
    });
});
