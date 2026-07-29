(() => {
// Selects the "Start Camera" button
const startBtn = document.getElementById('start-camera-btn');
// If not on the home page, exit early
if (!startBtn) return;
// scanner variable
let html5QrcodeScanner;
// scan logic

// add input box for minutes, and a manula isbn input box
async function getData(isbn) {
    const url = `api/book/${isbn}`;

// Show loading spinner, hide scan content
document.getElementById('content-scan').classList.add('hidden');
document.getElementById('loading-section').classList.remove('hidden');

// what to do with data that is given back
try{
    const response = await fetch(url, {
        method: 'GET',
    });
    if (!response.ok) {
        console.log(`error getting data with api${response.status}`)
        // Hide loading, restore scan content
        document.getElementById('loading-section').classList.add('hidden');
        document.getElementById('content-scan').classList.remove('hidden');
        return;
    }

    const data = await response.json();
    console.log(data);

    // Populate the book data fields
    document.getElementById('book-data-title').value = data.title || '';
    document.getElementById('book-data-author').value = data.author || '';
    document.getElementById('book-data-genre').value = data.genre || '';

    // Show cover image if available
    const coverImg = document.getElementById('book-data-cover');
    if (data.cover) {
        coverImg.src = data.cover;
        coverImg.style.display = 'block';
    } else {
        coverImg.style.display = 'none';
    }

    // Hide loading, show book data section
    document.getElementById('loading-section').classList.add('hidden');
    document.getElementById('book-data-section').classList.remove('hidden');

} catch (error) {
    console.error("Error fetching book:", error.message);
    // Hide loading, restore scan content
    document.getElementById('loading-section').classList.add('hidden');
    document.getElementById('content-scan').classList.remove('hidden');
  }
}


function onScanSuccess(decodedText) {
    alert("ISBN found: " + decodedText);

    // stops cam after scan is done
    html5QrcodeScanner.clear();
    startBtn.classList.remove('hidden');
    document.getElementById('manual-isbn-box').classList.add('hidden');

   try {
    getData(decodedText);
   } catch (error) {
    console.error("Error fetching book:", error.message);
   }
   

}
// on-press for cam button
startBtn.addEventListener('click', () => {
    startBtn.classList.add('hidden');
    // Show manual ISBN fallback
    document.getElementById('manual-isbn-box').classList.remove('hidden');
    // define type of barcode we want to scan
    const formats = [
        Html5QrcodeSupportedFormats.EAN_13,
        Html5QrcodeSupportedFormats.EAN_8
    ]


    // initializes scanner obj/lib
    html5QrcodeScanner = new Html5QrcodeScanner(
        "interactive-scanner", // renders cam feed
        { 
            fps: 15,
            qrbox: { width: 350, height: 150 },
            formatsToSupport: formats,
            rememberLastUsedCamera: true,
            showTorchButtonIfSupported: true,
            // Barcodes don't need mirror/flip
            disableFlip: true,
            // Request HD camera so barcode lines are sharp and clear
            videoConstraints: {
                facingMode: "environment",
                width: { min: 640, ideal: 1280 },
                height: { min: 480, ideal: 720 }
            },
            // Use the browser's native BarcodeDetector if available (Chrome/Safari)
            experimentalFeatures: {
                useBarCodeDetectorIfSupported: true
            }
        }
    );

    // start scanning
    html5QrcodeScanner.render(onScanSuccess);
})

// Manual ISBN Look Up button
document.getElementById('manual-isbn-submit').addEventListener('click', () => {
    const isbn = document.getElementById('manual-isbn-input').value.trim();
    if (isbn.length === 0 || isbn.length > 13) {
        alert('ISBNs can only be between 10-13 numbers long');
        return;
    } else if (/[^\d\s]/.test(isbn)) {
        alert('No letters or symbols are accepted, only numbers');
        return;
    }
    try{
        onScanSuccess(isbn);
    } catch (error) {
        console.error("Error fetching book:", error.message);
    }
    
})

// Done button — hide book data, show scan content again
document.getElementById('book-data-done').addEventListener('click', () => {
    // Hide any previous warnings
    document.getElementById('warning-empty').classList.add('hidden');
    document.getElementById('only-nums-minutes').classList.add('hidden');

    const data = {
        title: document.getElementById('book-data-title').value.trim().toLowerCase(),
        author: document.getElementById('book-data-author').value.trim().toLowerCase(),
        genre: document.getElementById('book-data-genre').value.trim().toLowerCase(),
        minutes: document.getElementById('book-data-minutes').value.trim()
    };

    if (data.title.length === 0 || data.author.length === 0 || data.genre.length === 0 || data.minutes.length === 0) {
        document.getElementById('only-nums-minutes').classList.add('hidden');
        document.getElementById('warning-empty').classList.remove('hidden');
        return;
    } else if (!/^\d+$/.test(data.minutes)) {
        document.getElementById('warning-empty').classList.add('hidden');
        document.getElementById('only-nums-minutes').classList.remove('hidden');
        return;
    } else {
        fetch("/api/book/save", {
            method: "POST",
            headers:{
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (response.ok) {
                // reload the page so updated logs show
                window.location.reload();
            } else {
                return response.json().then(err => {
                    alert("Error saving log: " + err.error);
                });
            }
        })
        .catch(error => {
            console.error("Network error: ", error);
        });
    }
    console.log(data)
    document.getElementById('book-data-minutes').value = '';
    // hides data input content
    document.getElementById('book-data-section').classList.add('hidden');
    // adds back the content scan stuff
    document.getElementById('content-scan').classList.remove('hidden');
    // brings back camera button
    startBtn.classList.remove('hidden');
    // hides manual input
    document.getElementById('manual-isbn-box').classList.add('hidden');
    document.getElementById('manual-isbn-input').value = '';



    // where we add data to db, remember to converts minutes to numbers
    

})
})();


// add data to db