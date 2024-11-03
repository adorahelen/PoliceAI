document.addEventListener("DOMContentLoaded", () => {
    fetch('/api/articles')
        .then(response => response.json())
        .then(data => {
            const articlesList = document.getElementById('articles-list');
            data.forEach(article => {
                const articleElement = document.createElement('div');
                articleElement.classList.add('article');
                articleElement.innerHTML = `
                    <h2>${article.title}</h2>
                    <p><strong>Author:</strong> ${article.author}</p>
                    <p><strong>Content:</strong> ${article.content}</p>
                `;

                // Add images if available
                if (article.files.length > 0) {
                    const filesElement = document.createElement('div');
                    filesElement.innerHTML = "<h3>Files:</h3>";
                    article.files.forEach(file => {
                        const fileElement = document.createElement('div');
                        fileElement.classList.add('file');
                        if (file.image_data) {
                            fileElement.innerHTML = `<img src="${file.image_data}" alt="${file.original_file_name}" style="width:200px;height:auto;">`;
                        } else {
                            fileElement.innerHTML = `<p>No image available for ${file.original_file_name}</p>`;
                        }
                        filesElement.appendChild(fileElement);
                    });
                    articleElement.appendChild(filesElement);
                }

                articlesList.appendChild(articleElement);
            });
        })
        .catch(error => console.error('Error fetching articles:', error));
});