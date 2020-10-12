package api

// Header is a responce header.
type Header struct {
	Status    string `json:"status"`
	ErrorCode int    `json:"error_code"`
}

// Error represents error details.
type Error struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
}

// Response is an object for returning to request.
type Response struct {
	Header  Header      `json:"header"`
	Content interface{} `json:"content"`
	Error   Error       `json:"error"`
}
