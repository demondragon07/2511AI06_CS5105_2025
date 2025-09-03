#include <bits/stdc++.h>
using namespace std;

class DisjointSet {
public:
    vector<int> parent, size, rank;
    DisjointSet(int n) {
        parent.resize(n+1);
        size.resize(n+1);
        rank.resize(n+1,0);
        for(int i=0;i<=n;i++){
            parent[i]=i;
            size[i]=1;
        }
    }

    int findUltParent(int node){
        if(parent[node]==node) return node;
        return parent[node] = findUltParent(parent[node]); // path compression
    }

    void unionByRank(int u, int v){
        int ulp_u= findUltParent(u);
        int ulp_v= findUltParent(v);

        if(ulp_u == ulp_v) return;

        if(rank[ulp_u] < rank[ulp_v]){
            parent[ulp_u]= ulp_v;
        }
        else if(rank[ulp_u] > rank[ulp_v]){
            parent[ulp_v]= ulp_u;
        } else {
            parent[ulp_v]= ulp_u;
            rank[ulp_u]++;
        }
    }

    void unionBySize(int u, int v){
        int ulp_u= findUltParent(u);
        int ulp_v= findUltParent(v);

        if(ulp_u == ulp_v) return;

        if(size[ulp_u] < size[ulp_v]){
            parent[ulp_u]= ulp_v;
            size[ulp_v] += size[ulp_u];
        } else {
            parent[ulp_v] = ulp_u;
            size[ulp_u] += size[ulp_v];
        }
    }
};

class Solution {
public:
    int removeStones(vector<vector<int>>& stones) {
        int maxrow=0 , maxcol=0, n=stones.size();
        for(auto it: stones){
            maxrow= max(maxrow, it[0]);
            maxcol= max(maxcol, it[1]);
        }

        DisjointSet ds(maxrow+maxcol+1);
        unordered_map<int,int> stonecells;

        for(auto it:stones){ 
            int noderow= it[0];
            int nodecol= it[1]+ maxrow+1;

            ds.unionBySize(noderow,nodecol);
            stonecells[noderow] = 1;
            stonecells[nodecol] = 1;
        }

        int comp=0;
        for(auto it: stonecells){
            if(ds.findUltParent(it.first)==it.first) comp++;
        }
        return n-comp;
    }
};

