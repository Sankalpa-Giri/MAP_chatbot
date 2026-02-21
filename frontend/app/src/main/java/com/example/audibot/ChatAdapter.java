package com.example.audibot;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.recyclerview.widget.RecyclerView;
import java.util.List;

public class ChatAdapter extends RecyclerView.Adapter<ChatAdapter.ViewHolder>{

    List<Message> messageList;

    public ChatAdapter(List<Message> messageList){
        this.messageList = messageList;
    }

    @Override
    public int getItemViewType(int position){
        return messageList.get(position).isUser() ? 1 : 0;
    }

    public static class ViewHolder extends RecyclerView.ViewHolder{
        TextView msg;

        public ViewHolder(View v){
            super(v);

            msg = v.findViewById(R.id.user_msg);
            if(msg == null){
                msg = v.findViewById(R.id.bot_msg);
            }
        }
    }


    @Override
    public ViewHolder onCreateViewHolder(ViewGroup parent,int viewType){

        View view;

        if(viewType==1){
            view = LayoutInflater.from(parent.getContext())
                    .inflate(R.layout.item_user,parent,false);
        }else{
            view = LayoutInflater.from(parent.getContext())
                    .inflate(R.layout.item_bot,parent,false);
        }

        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(ViewHolder holder,int position){
        holder.msg.setText(messageList.get(position).getText());
    }

    @Override
    public int getItemCount(){
        return messageList.size();
    }
}
