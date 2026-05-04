function nextStep(step) {
    // Validate current step before proceeding
    const currentStep = document.querySelector('.form-step.active');
    if (step > parseInt(currentStep.id.replace('step', ''))) { // Only validate if going forward
        const inputs = currentStep.querySelectorAll('input[required], select[required]');
        let isValid = true;
        inputs.forEach(input => {
            if (!input.checkValidity()) {
                input.reportValidity();
                isValid = false;
            }
        });
        if (!isValid) return;
    }

    // Hide all steps
    document.querySelectorAll('.form-step').forEach(el => el.classList.remove('active'));
    // Show target step
    document.getElementById('step' + step).classList.add('active');
}

// Handle "Other" allergy checkbox
document.getElementById('other_allergy_check').addEventListener('change', function () {
    const input = document.getElementById('other_allergy_input');
    input.disabled = !this.checked;
    if (this.checked) input.focus();
});

async function submitForm() {
    // Show loading state
    document.getElementById('fitnessForm').style.display = 'none';
    document.getElementById('loading').classList.remove('hidden');

    // Collect data
    const formData = new FormData(document.getElementById('fitnessForm'));
    const data = Object.fromEntries(formData.entries());

    // Handle checkboxes (allergies) manually as Object.fromEntries only takes the last one
    const allergies = [];
    document.querySelectorAll('input[name="allergies"]:checked').forEach(cb => {
        allergies.push(cb.value);
    });
    if (document.getElementById('other_allergy_check').checked) {
        allergies.push(document.getElementById('other_allergy_input').value);
    }
    data.allergies = allergies;

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });

        const result = await response.json();

        if (result.status === 'success') {
            // Redirect to results page (we'll implement this route next)
            // For now, let's just log it or simulate a redirect if we were using a real redirect
            // But since we are building a SPA-like feel or separate page, let's assume we render a new template
            // Actually, usually we'd redirect. Let's make the backend return a redirect URL or render the template directly.
            // For this flow, let's assume we replace the body or redirect.
            // Let's use document.write for simplicity or redirect to a result ID.
            // Better: Store data in session/localstorage and redirect.
            // OR: The backend renders the result template directly? No, it's an AJAX call.
            // Let's change the backend to render_template on POST? No, that's not RESTful.
            // Let's have the backend return the HTML or data.
            // Plan: Backend returns JSON data. Frontend redirects to /result?data=... (too long)
            // Plan: Backend stores result in session, returns "redirect": "/result".

            // For now, let's just assume the backend returns the data and we replace the content.
            // Or better, submit as a normal form? No, we want the loading spinner.

            // Let's do:
            window.location.href = '/result'; // The backend will serve the result from session
        } else {
            alert('Error generating plan: ' + result.message);
            location.reload();
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
        location.reload();
    }
}
