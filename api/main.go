package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"strconv"

	"github.com/Lazialize/gsapi/api"
	"github.com/gorilla/mux"

	_ "github.com/lib/pq"
)

const (
	host = "db"
	port = 5432
)

var gsapi *api.GSApi
var err error

func main() {
	user := os.Getenv("POSTGRES_USER")
	password := os.Getenv("POSTGRES_PASSWORD")
	db := os.Getenv("POSTGRES_DB")

	gsapi, err = api.New(host, user, password, db, port)
	checkError(err)
	defer gsapi.Close()
	handleRequest()
}

func createUserData(w http.ResponseWriter, r *http.Request) {

}

func fetchUserData(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)

	guildID, _ := strconv.Atoi(vars["guild_id"])
	userID, _ := strconv.Atoi(vars["user_id"])

	userData, err := gsapi.FetchUserData(guildID, userID)
	checkError(err)

	res := constructResponce(err == nil, []api.UserData{userData}, err)

	json.NewEncoder(w).Encode(res)
}

func fetchGuildAllUserData(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	guildID, _ := strconv.Atoi(vars["guild_id"])

	userData, err := gsapi.FetchGuildAllUserData(guildID)
	checkError(err)

	json.NewEncoder(w).Encode(userData)
}

func handleRequest() {
	router := mux.NewRouter().StrictSlash(true)
	router.HandleFunc("/userdata/{guild_id}/members/{user_id}", fetchUserData)
	router.HandleFunc("/userdata/{guild_id}/members", fetchGuildAllUserData)
	log.Fatal(http.ListenAndServe(":8081", router))
}

func checkError(err error) {
	if err != nil {
		// TODO: Using panic is very bad. I MUST think about the solution.
		panic(err)
	}
}

func constructResponce(status bool, content interface{}, err error) api.Response {
	var _status string

	if status {
		_status = "Ok"
	} else {
		_status = "Ng"
	}

	var errorCode int
	if err == nil {
		errorCode = 0
	} else {
		errorCode = 1
	}

	header := api.Header{
		Status:    _status,
		ErrorCode: errorCode,
	}

	return api.Response{
		Header:  header,
		Content: content,
	}
}
