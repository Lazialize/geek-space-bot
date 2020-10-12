package api

import (
	"database/sql"
	"fmt"
	"time"
)

// GSApi has methods that database operation.
type GSApi struct {
	DB *sql.DB
}

// New is a constructor of the GSApi.
func New(host, user, password, dbname string, port int) (*GSApi, error) {
	psqlDsn := fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s sslmode=disable", host, port, user, password, dbname)
	db, err := sql.Open("postgres", psqlDsn)

	if err != nil {
		return nil, err
	}

	count := 0

retry:
	err = db.Ping()
	if err != nil && count < 5 {
		count++
		time.Sleep(2 * time.Second)
		goto retry
	}

	if err != nil {
		return nil, err
	}
	fmt.Println("Connected!")

	return &GSApi{DB: db}, nil
}

// FetchUserData returns the user's UserData in a guild that is retrieved by the guildID and the userID.
func (t GSApi) FetchUserData(guildID, userID int) (UserData, error) {
	query := `
		SELECT *
		FROM USER_DATA
		WHERE guild_id = $1 AND user_id = $2;`

	row := t.DB.QueryRow(query, guildID, userID)

	var ID int
	var gID int
	var uID int
	var ownExp int
	var nextExp int
	var totalExp int

	err := row.Scan(&ID, &gID, &uID, &ownExp, &nextExp, &totalExp)
	if err != nil {
		return UserData{}, err
	}

	return UserData{ID: ID, GuildID: guildID, UserID: userID, OwnExp: ownExp, NextExp: nextExp, TotalExp: totalExp}, nil
}

// FetchGuildAllUserData returns all user's UserData in a guild that is retrieved by the guildID.
func (t GSApi) FetchGuildAllUserData(guildID int) (*[]UserData, error) {
	query := `
		SELECT *
		FROM USER_DATA
		WHERE guild_id = $1;`
	rows, err := t.DB.Query(query, guildID)
	if err != nil {
		return nil, err
	}

	userData := []UserData{}

	for rows.Next() {
		var ID int
		var gID int
		var uID int
		var ownExp int
		var nextExp int
		var totalExp int

		err = rows.Scan(&ID, &gID, &uID, &ownExp, &nextExp, &totalExp)
		if err != nil {
			continue
		}
		userData = append(userData, UserData{ID: ID, GuildID: gID, UserID: uID, OwnExp: ownExp, NextExp: nextExp, TotalExp: totalExp})
	}

	return &userData, nil
}

// Close closes database handle.
func (t GSApi) Close() {
	t.DB.Close()
}
