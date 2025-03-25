document.getElementById('registerForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch('http://127.0.0.1:5000/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })  // Chuyển object thành JSON
        });

        const data = await response.json();
        
        if (response.ok) {

            // Thông báo thành công
            alert("Đăng ký thành công! Bạn sẽ được chuyển đến trang đăng nhập.");

            // Chuyển hướng sau 2 giây
            setTimeout(() => {
                window.location.href = "/login";  // Chỉnh sửa đường dẫn nếu cần
            }, 2000);
        } else {
            alert("Lỗi: " + (data.error || "Không thể đăng ký"));
        }
    } catch (error) {
        alert("Có lỗi xảy ra, vui lòng thử lại!");
        console.error(error);
    }
});
