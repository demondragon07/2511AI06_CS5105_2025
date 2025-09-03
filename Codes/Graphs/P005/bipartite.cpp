#include <iostream>
#include <vector>
using namespace std;

class Solution {
public:
    bool dfsBipartite(vector<vector<int>> &adj, vector<int> &col, int node, int color) {
        col[node] = color;

        for (int neigh : adj[node]) {
            if (col[neigh] == -1) {
                if (dfsBipartite(adj, col, neigh, !color) == false) 
                    return false;
            } 
            else if (col[neigh] == col[node]) {
                return false; // Conflict
            }
        }
        return true;
    }

    bool isBipartite(vector<vector<int>>& graph) {
        int n = graph.size();
        vector<int> col(n, -1);

        for (int i = 0; i < n; i++) {
            if (col[i] == -1) {
                if (dfsBipartite(graph, col, i, 0) == false) 
                    return false;
            }
        }
        return true;
    }
};

