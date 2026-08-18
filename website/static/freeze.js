const buyBtn = document.getElementById('btn-buy-freeze');
buyBtn.addEventListener('click', (event) => {
    //hide any previously displayed alert messages
    document.getElementById("buy-freeze-good").classList.add('hidden');
    document.getElementById("buy-freeze-err-coins").classList.add('hidden');
    document.getElementById("buy-freeze-err-max").classList.add('hidden');
    document.getElementById("buy-freeze-err-network").classList.add('hidden');
    fetch('/streak/buy/freeze', {
        method: 'POST',
    })
    .then(response => {
        if (response.ok) {
            return response.text(); //convert response stream to text string
        }
        throw new Error('Network response was not ok');
    })
    .then(data => {
        if (data === 'success') {
            //increment the freeze counter text
            const countEl = document.getElementById("modal-freeze-count");
            const headerCountEl = document.getElementById("header-freeze-count");
            const currentVal = parseInt(countEl.textContent) || 0;

            const coinAmount = document.getElementById('header-coin-count');
            const currentValue = parseInt(coinAmount.textContent) || 0;
            
            countEl.textContent = currentVal + 1;
            if (headerCountEl) headerCountEl.textContent = currentVal + 1;

            coinAmount.textContent = currentValue - 250;

            document.getElementById("buy-freeze-good").classList.remove('hidden');
        } else if (data === 'not-enough') {
            document.getElementById("buy-freeze-err-coins").classList.remove('hidden');
        } else if (data === 'max') {
            document.getElementById("buy-freeze-err-max").classList.remove('hidden');
        }
    })
    .catch(error => {
        console.error("error buying: ", error);
        document.getElementById("buy-freeze-err-network").classList.remove('hidden');
    });
});