
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const instagramTab = document.getElementById('instagram-tab');
    const youtubeTab = document.getElementById('youtube-tab');
    const urlInput = document.getElementById('url-input');
    const mp4Option = document.getElementById('mp4-option');
    const mp3Option = document.getElementById('mp3-option');
    const checkButton = document.getElementById('check-button');
    const resultContainer = document.getElementById('result-container');
    const downloadButton = document.getElementById('download-button');
    const youtubeContentTypes = document.getElementById('youtube-content-types');
    const instagramContentTypes = document.getElementById('instagram-content-types');
    const regularVideo = document.getElementById('regular-video');
    const shorts = document.getElementById('shorts');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const videoTitle = document.getElementById('video-title');
    const videoDuration = document.getElementById('video-duration');
    const videoQuality = document.getElementById('video-quality');
    const videoPreview = document.getElementById('video-preview');
    const downloadBurst = document.getElementById('download-burst');
    
    // Instagram content types
    const postsType = document.getElementById('posts-type');
    const storiesType = document.getElementById('stories-type');
    const reelsType = document.getElementById('reels-type');
    const highlightsType = document.getElementById('highlights-type');
    const profileType = document.getElementById('profile-type');
    const imagesType = document.getElementById('images-type');
    
    // Tab switching
    instagramTab.addEventListener('click', function() {
        instagramTab.classList.add('active');
        youtubeTab.classList.remove('active');
        instagramContentTypes.style.display = 'flex';
        youtubeContentTypes.style.display = 'none';
        updatePlaceholder();
    });
    
    youtubeTab.addEventListener('click', function() {
        youtubeTab.classList.add('active');
        instagramTab.classList.remove('active');
        instagramContentTypes.style.display = 'none';
        youtubeContentTypes.style.display = 'flex';
        updatePlaceholder();
    });
    
    // Instagram content type switching
    function resetInstagramContentTypes() {
        postsType.classList.remove('active');
        storiesType.classList.remove('active');
        reelsType.classList.remove('active');
        highlightsType.classList.remove('active');
        profileType.classList.remove('active');
        imagesType.classList.remove('active');
    }
    
    postsType.addEventListener('click', function() {
        resetInstagramContentTypes();
        postsType.classList.add('active');
        updatePlaceholder();
    });
    
    storiesType.addEventListener('click', function() {
        resetInstagramContentTypes();
        storiesType.classList.add('active');
        updatePlaceholder();
    });
    
    reelsType.addEventListener('click', function() {
        resetInstagramContentTypes();
        reelsType.classList.add('active');
        updatePlaceholder();
    });
    
    highlightsType.addEventListener('click', function() {
        resetInstagramContentTypes();
        highlightsType.classList.add('active');
        updatePlaceholder();
    });
    
    profileType.addEventListener('click', function() {
        resetInstagramContentTypes();
        profileType.classList.add('active');
        updatePlaceholder();
    });
    
    imagesType.addEventListener('click', function() {
        resetInstagramContentTypes();
        imagesType.classList.add('active');
        updatePlaceholder();
    });
    
    // YouTube content type switching
    regularVideo.addEventListener('click', function() {
        regularVideo.classList.add('active');
        shorts.classList.remove('active');
        updatePlaceholder();
    });
    
    shorts.addEventListener('click', function() {
        shorts.classList.add('active');
        regularVideo.classList.remove('active');
        updatePlaceholder();
    });
    
    // Format option switching
    mp4Option.addEventListener('click', function() {
        mp4Option.classList.add('active');
        mp3Option.classList.remove('active');
        updateDownloadButtonText();
    });
    
    mp3Option.addEventListener('click', function() {
        mp3Option.classList.add('active');
        mp4Option.classList.remove('active');
        updateDownloadButtonText();
    });
    
    // Update placeholder based on active tab and content type
    function updatePlaceholder() {
        if (instagramTab.classList.contains('active')) {
            if (postsType.classList.contains('active')) {
                urlInput.placeholder = 'https://www.instagram.com/p/...';
            } else if (storiesType.classList.contains('active')) {
                urlInput.placeholder = 'https://www.instagram.com/stories/...';
            } else if (reelsType.classList.contains('active')) {
                urlInput.placeholder = 'https://www.instagram.com/reels/...';
            } else if (highlightsType.classList.contains('active')) {
                urlInput.placeholder = 'https://www.instagram.com/stories/highlights/...';
            } else if (profileType.classList.contains('active')) {
                urlInput.placeholder = 'https://www.instagram.com/username/';
            } else if (imagesType.classList.contains('active')) {
                urlInput.placeholder = 'https://www.instagram.com/p/...';
            }
        } else {
            if (regularVideo.classList.contains('active')) {
                urlInput.placeholder = 'https://www.youtube.com/watch?v=...';
            } else {
                urlInput.placeholder = 'https://www.youtube.com/shorts/...';
            }
        }
    }
    
    // Update download button text
    function updateDownloadButtonText() {
        let downloadText = 'Download ';
        
        if (instagramTab.classList.contains('active')) {
            if (postsType.classList.contains('active')) {
                downloadText += mp3Option.classList.contains('active') ? 'Post Audio' : 'Post Video';
            } else if (storiesType.classList.contains('active')) {
                downloadText += mp3Option.classList.contains('active') ? 'Story Audio' : 'Story';
            } else if (reelsType.classList.contains('active')) {
                downloadText += mp3Option.classList.contains('active') ? 'Reel Audio' : 'Reel';
            } else if (highlightsType.classList.contains('active')) {
                downloadText += mp3Option.classList.contains('active') ? 'Highlight Audio' : 'Highlight';
            } else if (profileType.classList.contains('active')) {
                downloadText += 'Profile Picture';
            } else if (imagesType.classList.contains('active')) {
                downloadText += 'Image';
            }
        } else {
            if (shorts.classList.contains('active')) {
                downloadText += mp3Option.classList.contains('active') ? 'Shorts Audio' : 'Shorts Video';
            } else {
                downloadText += mp3Option.classList.contains('active') ? 'Audio' : 'Video';
            }
        }
        
        if (downloadButton) {
            downloadButton.textContent = downloadText;
        }
    }
    
    // Check button functionality
    checkButton.addEventListener('click', function() {
        const url = urlInput.value.trim();
        
        if (!url) {
            alert('Please enter a valid URL');
            return;
        }
        
        // Show loading state
        checkButton.textContent = 'Checking...';
        checkButton.disabled = true;
        
        // Make request to /check endpoint
        const formData = new FormData();
        formData.append('url', url);
        
        // fetch('/check', {
        //     method: 'POST',
        //     body: formData
        // })
        // .then(response => {
        //     if (!response.ok) {
        //         throw new Error('Failed to check media');
        //     }
        //     return response.json();
        // })
        // .then(data => {
        //     if (data.error) {
        //         throw new Error(data.error);
        //     }
            
        //     // Reset button
        //     checkButton.textContent = 'Check Media';
        //     checkButton.disabled = false;
            
        //     // Update video info
        //     videoTitle.textContent = data.title || 'Unknown Title';
        //     const duration = data.duration || 0;
        //     const minutes = Math.floor(duration / 60);
        //     const seconds = Math.floor(duration % 60);
        //     videoDuration.textContent = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
        //     videoQuality.textContent = data.quality || 'Unknown Quality';
        //     videoPreview.src = data.thumbnail || '';
            
        //     // Show result
        //     resultContainer.classList.add('show');
            
        //     // Update download button text
        //     updateDownloadButtonText();
        // })
        // .catch(error => {
        //     console.error('Error:', error);
        //     alert('Failed to check media: ' + error.message);
        //     checkButton.textContent = 'Check Media';
        //     checkButton.disabled = false;
        // });
        fetch('/check', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Failed to check media');
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            // Rest of the code to display metadata...
            document.getElementById('metadata').innerHTML = `
                <p>Title: ${data.title}</p>
                <p>Duration: ${data.duration} seconds</p>
                <p>Quality: ${data.quality}</p>
                <img src="${data.thumbnail}" alt="Thumbnail" style="max-width: 200px;">
            `;
            downloadButton.disabled = false;
            checkButton.textContent = 'Check Media';
            checkButton.disabled = false;
        })
        .catch(error => {
            console.error('Error:', error);
            alert(error.message);  // Display the specific error message
            checkButton.textContent = 'Check Media';
            checkButton.disabled = false;
        });
    });
    
    // Generate burst particles
    function createBurstEffect() {
        downloadBurst.innerHTML = '';
        downloadBurst.classList.add('show');
        
        const centerX = window.innerWidth / 2;
        const centerY = window.innerHeight / 2;
        const colors = ['#e94057', '#f27121', '#8a2387', '#ffffff'];
        
        for (let i = 0; i < 50; i++) {
            const particle = document.createElement('div');
            particle.classList.add('burst-particle');
            
            const angle = Math.random() * Math.PI * 2;
            const distance = Math.random() * Math.min(window.innerWidth, window.innerHeight) * 0.5;
            const x = centerX + Math.cos(angle) * distance;
            const y = centerY + Math.sin(angle) * distance;
            
            const size = Math.random() * 20 + 10;
            const color = colors[Math.floor(Math.random() * colors.length)];
            
            particle.style.width = `${size}px`;
            particle.style.height = `${size}px`;
            particle.style.left = `${x}px`;
            particle.style.top = `${y}px`;
            particle.style.background = color;
            
            particle.style.animation = `burstAnimation ${Math.random() * 1 + 0.5}s forwards`;
            
            downloadBurst.appendChild(particle);
        }
        
        setTimeout(() => {
            downloadBurst.classList.remove('show');
        }, 1500);
    }
    
    // Download button functionality
    downloadButton.addEventListener('click', function(e) {
        e.preventDefault();
        const url = urlInput.value.trim();
        const format = mp3Option.classList.contains('active') ? 'mp3' : 'mp4';
        
        if (!url) {
            alert('Please enter a valid URL');
            return;
        }
        
        // Add downloading class
        downloadButton.classList.add('downloading');
        downloadButton.textContent = 'Downloading...';
        
        // Show progress
        progressContainer.classList.add('show');
        
        // Simulate progress (since we can't track real progress easily)
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 10;
            if (progress > 100) progress = 100;
            
            progressBar.style.width = `${progress}%`;
            
            if (progress === 100) {
                clearInterval(interval);
            }
        }, 200);
        
        // Make request to /download endpoint
        const formData = new FormData();
        formData.append('url', url);
        formData.append('format', format);
        
        fetch('/download', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Download failed: ' + response.statusText);
            }
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `media.${format}`;
            if (contentDisposition) {
                const match = contentDisposition.match(/filename="(.+)"/);
                if (match) filename = match[1];
            }
            return response.blob().then(blob => ({ blob, filename }));
        })
        .then(({ blob, filename }) => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            
            // Show burst effect
            createBurstEffect();
            
            setTimeout(() => {
                downloadButton.classList.remove('downloading');
                downloadButton.textContent = 'Download Complete!';
                
                // Hide progress after completion
                setTimeout(() => {
                    progressContainer.classList.remove('show');
                    progressBar.style.width = '0';
                    
                    // Reset after a delay
                    setTimeout(() => {
                        updateDownloadButtonText();
                    }, 1500);
                }, 500);
            }, 500);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to download: ' + error.message);
            downloadButton.classList.remove('downloading');
            downloadButton.textContent = 'Download Failed';
            progressContainer.classList.remove('show');
            progressBar.style.width = '0';
        });
    });
    
    // Initialize placeholder
    updatePlaceholder();
});
