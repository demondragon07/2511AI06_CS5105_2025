#include<iostream>
#include<vector>
#include<queue>

using namespace std;

vector<int> bfs(vector<vector<int>> adj, int v){
  vector<int> vis(v,0);
  vector<int> ans;
  queue<int> q;

  vis[0]=1;
  q.push(0);

  while(!q.empty()){
    int curr= q.front();
    q.pop();
    ans.push_back(curr);

    for(auto it: adj[curr]){
      if(vis[it]!=1){
        q.push(it);
        vis[it]=1;
      }
    }
  }
  return ans;
}

