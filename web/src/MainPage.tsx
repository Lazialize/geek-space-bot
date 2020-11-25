import React from "react";
import logo from "./logo.svg";
import "./MainPage.css";

class MainPage extends React.Component {
  render() {
    return (
      <div className="background">
        <div className="header">
          <img src={logo} className="logo" alt="Logo"/>
          <h1>Geek Space</h1>
        </div>
        <div className="body">
          <h1>Geek Space Bot</h1>
          <div className="button" onClick={this.button}>Login</div>
        </div>
      </div>
    );
  }
}

export default MainPage;