document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("login-form");
  const submitBtn = document.getElementById("submit-btn");
  const githubBtn = document.getElementById("github-login-btn");
  const urlParams = new URLSearchParams(window.location.search);

  if (urlParams.get("registered") === "true") {
    const successMessage = document.getElementById("success-message");
    successMessage.classList.remove("hidden");
    setTimeout(() => successMessage.classList.add("hidden"), 5000);
  }

  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    submitBtn.disabled = true;
    submitBtn.textContent = "Signing in...";

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        document.cookie = `token=${data.token}; path=/; max-age=${60 * 60 * 24 * 7}; SameSite=Lax`;
        window.location.href = "/dashboard/";
      } else {
        console.error(data.message || "Login failed");
        submitBtn.disabled = false;
        submitBtn.textContent = "Sign in";
      }
    } catch (error) {
      console.error(error);
      submitBtn.disabled = false;
      submitBtn.textContent = "Sign in";
    }
  });

  githubBtn.addEventListener("click", async function () {
    try {
      const response = await fetch("/api/auth/github");
      const data = await response.json();

      if (data.auth_url) {
        window.location.href = data.auth_url;
      }
    } catch (error) {
      console.error(error);
    }
  });
});
