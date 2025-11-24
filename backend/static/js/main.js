document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("tts-form");
  const textArea = document.getElementById("tts-text");
  const langSelect = document.getElementById("tts-lang");
  const statusEl = document.getElementById("status");
  const audioContainer = document.getElementById("audio-container");
  const historyList = document.getElementById("history-list");
  const creditsSpan = document.getElementById("nav-credits");

  if (!form || !textArea || !langSelect) {
    console.warn("TTS form or fields not found in DOM.");
    return;
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();

    const text = textArea.value.trim();
    const lang = langSelect.value;

    if (!text) {
      statusEl.textContent = "Please enter some text first.";
      statusEl.className = "status status--error";
      return;
    }

    const payload = {
      text: text,
      lang: lang,
    };

    statusEl.textContent = "Generating audio...";
    statusEl.className = "status status--loading";

    // Optional: disable button while loading
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
      submitBtn.disabled = true;
    }

    fetch("/generate-audio", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    })
      .then(async (res) => {
        let data;
        try {
          data = await res.json();
        } catch (err) {
          throw new Error("Invalid JSON response from server");
        }

        if (!res.ok) {
          // Handle HTTP errors (400, 402, 500, etc.)
          if (data && data.error) {
            throw new Error(data.error);
          } else {
            throw new Error("Server error while generating audio.");
          }
        }

        return data;
      })
      .then((data) => {
        // If backend returns error field
        if (data.error) {
          statusEl.textContent = data.error;
          statusEl.className = "status status--error";
          return;
        }

        // ---------- Play new audio ----------
        if (data.audio_url) {
          audioContainer.innerHTML = `
            <audio controls src="${data.audio_url}"></audio>
          `;
        }

        // ---------- Update credits ----------
        if (data.remaining_credits !== undefined && creditsSpan) {
          creditsSpan.textContent = `Credits: ${data.remaining_credits}`;
        }

        // ---------- Update history ----------
        if (data.history && Array.isArray(data.history) && historyList) {
          historyList.innerHTML = "";
          data.history.forEach((item) => {
            const li = document.createElement("li");
            li.className = "history-item";
            li.innerHTML = `
              <div class="history-info">
                <div class="history-text">${item.text_preview}</div>
                <div class="history-meta">
                  <span>${(item.lang || "").toUpperCase()}</span>
                  <span>${item.timestamp || ""}</span>
                </div>
              </div>
              <audio controls src="${item.audio_url}"></audio>
            `;
            historyList.appendChild(li);
          });
        }

        statusEl.textContent = "Audio generated successfully.";
        statusEl.className = "status status--success";
      })
      .catch((err) => {
        console.error("TTS Error:", err);
        statusEl.textContent = err.message || "Something went wrong.";
        statusEl.className = "status status--error";
      })
      .finally(() => {
        if (submitBtn) {
          submitBtn.disabled = false;
        }
      });
  });
});
