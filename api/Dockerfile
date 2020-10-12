FROM 'golang'

WORKDIR /go/src/github.com/Lazialize/gsapi

COPY ./main.go .
COPY ./api ./api

RUN go get -u github.com/lib/pq
RUN go get -u github.com/gorilla/mux

EXPOSE 8081

RUN go build -o gsapi .

ENTRYPOINT [ "./gsapi" ]
