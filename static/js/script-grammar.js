// const apiKey = localStorage.getItem("api_key");
// if (!apiKey) {
//     console.error("API Key không tồn tại!");
// } else {
//     fetch("http://127.0.0.1:5000/grammar-check", {
//         method: "POST",
//         headers: {
//             "Content-Type": "application/json",
//             "Authorization": `Bearer ${apiKey}`
//         },
//         body: JSON.stringify({ text: "Đây là văn bản cần kiểm tra." })
//     })
//     .then(response => {
//         if (!response.ok) {
//             throw new Error(`HTTP error! Status: ${response.status}`);
//         }
//         return response.json();
//     })
//     .then(data => {
//         console.log("Kết quả kiểm tra:", data);
//         document.getElementById("result").innerText = "Kết quả: " + (data.result || "Không có kết quả");
//     })
//     .catch(error => console.error("Lỗi:", error));
// }