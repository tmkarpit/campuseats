# Assignment Output

This file records the main observed output from the commands and checks used for Assignment 1.

## HTTP request outputs

### `curl -i https://jsonplaceholder.typicode.com/posts/1`

```text
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 292

{
  "userId": 1,
  "id": 1,
  "title": "sunt aut facere repellat provident occaecati excepturi optio reprehenderit",
  "body": "quia et suscipit\nsuscipit recusandae consequuntur expedita et cum\nreprehenderit molestiae ut ut quas totam\nnostrum rerum est autem sunt rem eveniet architecto"
}
```

### `curl -i https://jsonplaceholder.typicode.com/comments/1`

```text
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 268

{
  "postId": 1,
  "id": 1,
  "name": "id labore ex et quam laborum",
  "email": "Eliseo@gardner.biz",
  "body": "laudantium enim quasi est quidem magnam voluptate ipsam eos\ntempora quo necessitatibus\ndolor quam autem quasi\nreiciendis et nam sapiente accusantium"
}
```

### `curl -i https://jsonplaceholder.typicode.com/users/1`

```text
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 509

{
  "id": 1,
  "name": "Leanne Graham",
  "username": "Bret",
  "email": "Sincere@april.biz",
  "address": {
    "street": "Kulas Light",
    "suite": "Apt. 556",
    "city": "Gwenborough",
    "zipcode": "92998-3874",
    "geo": {
      "lat": "-37.3159",
      "lng": "81.1496"
    }
  },
  "phone": "1-770-736-8031 x56442",
  "website": "hildegard.org",
  "company": {
    "name": "Romaguera-Crona",
    "catchPhrase": "Multi-layered client-server neural-net",
    "bs": "harness real-time e-markets"
  }
}
```

### `curl -i https://jsonplaceholder.typicode.com/todos/1`

```text
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 83

{
  "userId": 1,
  "id": 1,
  "title": "delectus aut autem",
  "completed": false
}
```

### `curl -i https://jsonplaceholder.typicode.com/posts/9999`

```text
HTTP/1.1 404 Not Found
Content-Type: application/json; charset=utf-8
Content-Length: 2

{}
```

## Network analysis output

Website tested: `https://www.iana.org/`

```text
Request count: 7
Total page size: 194,057 bytes
Slowest resource: https://www.iana.org/static/css/iana_website.3c174467e53c.css
Slowest resource time: 878 ms
3xx responses seen: none
4xx responses seen: none
```

## Git output

### `git status --short`

```text

```

No output means the working tree was clean.

### `git log --oneline --decorate`

```text
f4a13db (HEAD -> master) Add assignment HTTP and project brief files
a62b0cd Set up CampusEats repository
```
