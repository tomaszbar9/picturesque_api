# Picturesque API

### https://picturesque-r6r7.onrender.com

### Description:

**Picturesque API** is a REST API version of my CS50 final project **Picturesque**, which is a web application allowing a user to create a collection of posts matching literature quotes with photos. An example can a picture showing a place where the action takes place. That is why the website's users can also mark relevant places on the map. The full description of the Picturesque application is available [here](https://github.com/tomaszbar9/picturesque/blob/main/README.md) and there is also [a short video presentation on YouTube](https://www.youtube.com/watch?v=95eBI367RwE).

The API version of the application has all the functionalities of the previous one: a user can register, log in, create a post (uploading an image) and even 'mark' the place on the map by sending coordinates or an address. My goal was just to create a better structured and easier maintainable backend, and this time to deploy it.

The program is written in Python 3.11 using Flask Smorest framework, and is deployed on **render.com**. The images storing is managed by **Cloudinary.com**, a PostgreSQL database is hosted on **ElephantSQL.com**, and to store revoked access tokens I use redis service also on **render.com**.

The deployed application is currently populated by 'populate.py' script with random data.

The full API documentation is available here: https://picturesque-r6r7.onrender.com/swagger-ui

---

### Endpoints:

- /register

  `POST` - register user

  `DELETE` - remove account

- /login

  `POST` - authenticate user

- /logout

  `DELETE` - revoke JWT

- /refresh

  `POST` - get non-fresh token

- /users/<_id_>/posts

  `GET` - get all user's posts

- /users/<_id_>/collections

  `GET` - user's collections

- /users/recommendations

  `POST` - show recommendations for user (access token required)

- /posts [/?q=<_search phrase_>&page=<_int_>&page_size=<_int_>]

  `GET` - get all posts or by a search phrase (results paginated)

  `POST` - create post (access token required)

- /posts/<_id_>

  `GET` - get one post

  `PUT` - update post (access token required)

  `DELETE` - remove post (access token required)

- /authors

  `GET` - get all authors (results paginated)

- /authors/<_id_>

  `GET` - get one author

- /titles

  `GET` - get all titles (results paginated)

- /titles/<_id_>

  `GET` - get one title

- /collections/<_id_>

  `POST` - add post to user's collection (access token required)

  `DELETE` - remove post from user's collection (access token required)
