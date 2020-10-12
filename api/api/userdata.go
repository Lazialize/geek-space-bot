package api

// UserData represents the user's information about the member level.
type UserData struct {
	ID       int `json:"id"`
	GuildID  int `json:"guild_id"`
	UserID   int `json:"user_id"`
	OwnExp   int `json:"own_exp"`
	NextExp  int `json:"next_exp"`
	TotalExp int `json:"total_exp"`
}
