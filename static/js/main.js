document.addEventListener('DOMContentLoaded', () => {
  const imageInput = document.getElementById('image-input');
  const previewContainer = document.getElementById('preview-container');
  const resultDiv = document.getElementById('result');
  const spinner = document.querySelector('.spinner-border');
  const uploadForm = document.getElementById('upload-form');
  const analyzeButton = document.getElementById('analyze-button');
  const clearButton = document.getElementById('clear-button');

  imageInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
      // Client-side file type validation
      const allowedTypes = ['image/png', 'image/jpeg'];
      if (!allowedTypes.includes(file.type)) {
        displayError('Invalid file type. Please upload a PNG or JPEG image.');
        // Do not clear the input here, let the user see the invalid file selected
        previewContainer.innerHTML = '';
        return;
      }

      const reader = new FileReader();
      reader.onload = (event) => {
        previewContainer.innerHTML = `<img src="${event.target.result}" id="preview-image" alt="Image Preview">`;
      };
      reader.readAsDataURL(file);
      resultDiv.innerHTML = '';
    } else {
      previewContainer.innerHTML = '';
    }
  });

  clearButton.addEventListener('click', () => {
    uploadForm.reset();
    previewContainer.innerHTML = '';
    resultDiv.innerHTML = '';
    analyzeButton.disabled = false;
    analyzeButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true" style="display: none;"></span> Analyze';
  });

  uploadForm.addEventListener('submit', (e) => {
    e.preventDefault();
    console.log('Form submitted.');

    const file = imageInput.files[0];
    if (!file) {
      displayError('Please select a file.');
      console.log('No file selected.');
      return;
    }

    console.log('File selected:', file.name, file.type);

    const formData = new FormData();
    formData.append('image', file);
    console.log('FormData prepared.');

    spinner.style.display = 'block';
    analyzeButton.disabled = true;
    analyzeButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Analyzing...';
    resultDiv.innerHTML = '';

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/intensity', true);
    console.log('XHR opened.');

    xhr.onload = () => {
      console.log('XHR onload event fired. Status:', xhr.status);
      spinner.style.display = 'none';
      analyzeButton.disabled = false;
      analyzeButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true" style="display: none;"></span> Analyze';

      try {
        const data = JSON.parse(xhr.responseText);
        console.log('Response data:', data);
        if (xhr.status >= 200 && xhr.status < 300) {
          displayResult(data);
        } else {
          displayError(data.error);
        }
      } catch (error) {
        console.error('Error parsing JSON response:', error);
        displayError('An unexpected error occurred.');
      }
    };

    xhr.onerror = () => {
      console.error('XHR onerror event fired.');
      spinner.style.display = 'none';
      displayError('An error occurred during the upload.');
    };

    xhr.send(formData);
    console.log('XHR send called.');
  });

  function displayResult(data) {
    const fileSizeKB = (data.image_size_bytes / 1024).toFixed(2);
    resultDiv.innerHTML = `
            <div class="alert alert-success">
                <h5 class="alert-heading">Analysis Complete</h5>
                <hr>
                <p><strong>Filename:</strong> ${data.filename}</p>
                <p><strong>Average Intensity:</strong> ${data.average_intensity}</p>
                <p><strong>Image Dimensions:</strong> ${data.image_size[0]} x ${data.image_size[1]} pixels</p>
                <p><strong>Total Pixels:</strong> ${data.pixel_count.toLocaleString()}</p>
                <p><strong>Original Mode:</strong> ${data.original_mode}</p>
                <p><strong>File Size:</strong> ${fileSizeKB} KB</p>
                <p><strong>Process Time:</strong> ${data.duration_ms} ms</p>
            </div>
        `;
  }

  function displayError(message) {
    console.error('Displaying error:', message);
    resultDiv.innerHTML = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                <strong>Error:</strong> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
  }
});