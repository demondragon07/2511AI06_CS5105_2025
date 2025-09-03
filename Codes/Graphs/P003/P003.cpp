#include<iostream>
#include<vector>
#include<queue>

using namespace std;

int orangesRotting(vector<vector<int>>& grid) {
        int m = grid.size(), n = grid[0].size();

        //{ {row,col} , time }
        queue<pair<pair<int, int>, int>> q;

        // to not change the given structure grid, vis array is used
        vector<vector<int>> vis(m, vector<int>(n, 0));

        // to count number of fresh oranges so that at last we can say if any
        // fresh left or not
        int cfresh = 0;
        for (int i = 0; i < m; i++) {
            for (int j = 0; j < n; j++) {
                // push all rotten oranges in queue
                if (grid[i][j] == 2) {
                    q.push({{i, j}, 0});
                    vis[i][j] = 2;
                } else if (grid[i][j] == 1)
                    cfresh++;
            }
        }

        int time = 0, cnt = 0;

        // while queue is not emoty keep on inserting adjacent neighbours with
        // incremented time
        while (!q.empty()) {
            int row = q.front().first.first;
            int col = q.front().first.second;
            int t = q.front().second;
            q.pop();

            time = max(time, t);

            // new technique to traverse all neighbours in adjacent cells one by
            // one
            int delrow[] = {-1, 0, 1, 0};
            int delcol[] = {0, 1, 0, -1};

            for (int i = 0; i < 4; i++) {
                int nextrow = row + delrow[i];
                int nextcol = col + delcol[i];

                if (nextrow >= 0 && nextrow < m && nextcol >= 0 &&
                    nextcol < n && grid[nextrow][nextcol] == 1 &&
                    vis[nextrow][nextcol] != 2) {
                    q.push({{nextrow, nextcol}, t + 1});
                    cnt++;
                    // grid[nextrow][nextcol] = 2; -- no need to change the
                    // given structure grid
                    vis[nextrow][nextcol] = 2;
                }
            }
        }

        // if any fresh orange is left means cannot rot every fresh organges
        if (cnt != cfresh)
            return -1;

        return time;
}

