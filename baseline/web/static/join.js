const form = document.querySelector("[data-join-form]");
const steps = [...form.querySelectorAll("[data-join-step]")];
const progress = document.querySelector(".progress-strip");
const previous = form.querySelector("[data-previous]");
const next = form.querySelector("[data-next]");
const finish = form.querySelector("[data-finish]");

let activeStep = 0;
form.noValidate = true;
progress.hidden = false;

function showStep(index, moveFocus = true) {
    activeStep = index;
    steps.forEach((step, position) => {
        step.hidden = position !== index;
        const indicator = progress.children[position];
        indicator.classList.toggle("complete", position < index);
        if (position === index) {
            indicator.setAttribute("aria-current", "step");
        } else {
            indicator.removeAttribute("aria-current");
        }
    });
    previous.hidden = index === 0;
    next.hidden = index === steps.length - 1;
    finish.hidden = !next.hidden;
    if (moveFocus) {
        steps[index].querySelector("h2").focus();
    }
}

function firstInvalid(step) {
    return [...step.querySelectorAll("input")].find((input) => !input.validity.valid);
}

function advance() {
    const invalid = firstInvalid(steps[activeStep]);
    if (invalid) {
        invalid.reportValidity();
        return;
    }
    showStep(activeStep + 1);
}

previous.addEventListener("click", () => showStep(activeStep - 1));
next.addEventListener("click", advance);
form.addEventListener("submit", (event) => {
    if (activeStep < steps.length - 1) {
        event.preventDefault();
        advance();
        return;
    }

    for (const [index, step] of steps.entries()) {
        const invalid = firstInvalid(step);
        if (invalid) {
            event.preventDefault();
            showStep(index);
            invalid.reportValidity();
            return;
        }
    }

    finish.disabled = true;
    finish.textContent = "Placing demo order…";
});

window.addEventListener("pageshow", () => {
    if (finish.disabled) {
        finish.disabled = false;
        finish.textContent = "Place demo order →";
    }
});

const firstError = steps.findIndex((step) => step.querySelector(".field-error"));
showStep(Math.max(firstError, 0), false);
