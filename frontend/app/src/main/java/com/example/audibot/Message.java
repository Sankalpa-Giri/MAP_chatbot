package com.example.audibot;

public class Message {
    String text;
    boolean isUser;

    public Message(String text, boolean isUser){
        this.text = text;
        this.isUser = isUser;
    }

    public String getText(){
        return text;
    }

    public boolean isUser(){
        return isUser;
    }
}
