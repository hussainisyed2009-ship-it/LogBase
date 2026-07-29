// declaring variables for each element that we track
const btnScan = document.getElementById('btn-scan');
const btnManual = document.getElementById('btn-manual');

const contentsManual = document.getElementById('content-manual');
const contentsScan = document.getElementById('content-scan');

btnScan.addEventListener('click', () => {
    // updates when button is pressed
    btnScan.classList.add('active');
    btnManual.classList.remove('active');

    // updates content
    contentsScan.classList.remove('hidden');
    contentsManual.classList.add('hidden');
})

btnManual.addEventListener('click', () => {
    // updates when button is pressed
    btnScan.classList.remove('active');
    btnManual.classList.add('active');

    // updates content
    contentsScan.classList.add('hidden');
    contentsManual.classList.remove('hidden');

    // clear any scan state
    document.getElementById('book-data-section').classList.add('hidden');
    document.getElementById('loading-section').classList.add('hidden');
})