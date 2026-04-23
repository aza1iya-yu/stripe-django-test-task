document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.pay-button').forEach(function (button) {
        button.addEventListener('click', function () {
            const orderId = this.dataset.orderId;
            const currency = this.dataset.currency;
            const originalText = this.textContent;

            this.textContent = 'Processing...';
            this.disabled = true;

            fetch(`/buy/order/${orderId}/?currency=${currency}`)
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(err => Promise.reject(err));
                    }
                    return response.json();
                })
                .then(session => {
                    window.location.href = session.session_url;
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Payment error: ' + (error.error || error.message || 'Unknown error'));
                    this.textContent = originalText;
                    this.disabled = false;
                });
        });
    });
});
