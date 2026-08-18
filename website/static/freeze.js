const buyBtn = document.getElementById('btn-buy-freeze')

// listener for buying
buyBtn.addEventListener('click', (event) => {
    fetch('/streak/buy/freeze', {
        method: 'POST',
    })
    .then(response => {
        if (response.ok) {
            if (response == 'success') {
                document.getElementById("modal-freeze-count").value =+1;
                document.getElementById("buy-freeze-good").classList.remove('hidden');
            } else if (response == 'not-enough') {
                document.getElementById("buy-freeze-err-coins").classList.remove('hidden');
            } else if (response == 'max') {
                document.getElementById("buy-freeze-err-max").classList.remove('hidden');
            }
        } else {
            document.getElementById("buy-freeze-err-network").classList.remove('hidden');
        }
    })
        .catch(error => {
        console.error("error buying: ", error)
        document.getElementById("buy-freeze-err-network").classList.remove('hidden');
        })
})