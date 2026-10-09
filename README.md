Hello! This is my student blog web-application project built with Django (Backend) and styled with Bootstrap 5 (Frontend)
This project allows users to share their nature observations through custom posts embedded with media (images and video),
and engage with the community by liking and commenting on other users' content. Built as a Nature Blog, but can be adopted for other themes.

✨ Key Features

Content Management (CRUD): Authenticated users can create, view, update, and delete their own posts; like and unlike posts; write, view and delete their own comments.

Responsive Bootstrap Interface: Mobile-friendly UI built using Bootstrap layout utilities and components.

Containerized: You can run this web app in a Docker container.


🛠️ Tech Stack

• Backend Framework: Django (Python), Django Rest Framework

• Database: PostgreSQL

• Frontend: HTML, CSS, Bootstrap 5

• External Services: SMTP Email Server (Gmail)


🎨 Database Architecture (Data Model)

To give you an idea of how the application structures data, here are the primary database relationships:

• Category ↔ Post: One-to-Many (There can be multiple posts in a category).

• Post ↔ PostImage: One-to-Many (Several images can be uploaded to a post).

• User ↔ Post: One-to-Many (A user can create multiple posts).

• Post ↔ Comment: One-to-Many (There can be multiple comments to a post).

• User ↔ Comment: One-to-Many (A user can leave multiple comments to different posts).

• User ↔ Post (Likes): Many-to-Many (Many users can like many different posts).
