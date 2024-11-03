// Fetch user data and display it
async function fetchUsers() {
    try {
        const response = await fetch('/api/users'); // API URL 수정
        if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
        }
        const users = await response.json();

        const userList = document.getElementById('user-list');
        if (!userList) {
            console.error("User list element not found.");
            return;  // 함수 종료
        }

        userList.innerHTML = '';  // Clear any existing content

        users.forEach(user => {
            // Create a card for each user
            const userCard = document.createElement('div');
            userCard.className = 'user-card';

            // Profile Image
            const img = document.createElement('img');
            img.src = user.profile_image || 'default-profile.png';  // Default if no image
            img.alt = 'Profile Image';  // 이미지 대체 텍스트 추가
            userCard.appendChild(img);

            // User Info
            const userInfo = document.createElement('div');
            userInfo.className = 'user-info';

            const name = document.createElement('h2');
            name.textContent = user.nickname || 'Unknown User';
            userInfo.appendChild(name);

            const email = document.createElement('p');
            email.textContent = `Email: ${user.email}`;
            userInfo.appendChild(email);

            const role = document.createElement('p');
            role.textContent = `Role: ${user.role}`;
            userInfo.appendChild(role);

            if (user.profile_url) {
                const profileLink = document.createElement('a');
                profileLink.href = user.profile_url;
                profileLink.textContent = 'Profile Link';
                profileLink.target = '_blank';
                userInfo.appendChild(profileLink);
            }

            userCard.appendChild(userInfo);
            userList.appendChild(userCard);
        });
    } catch (error) {
        console.error('Error fetching users:', error);
    }
}

// Load user data when the page loads
document.addEventListener('DOMContentLoaded', fetchUsers);