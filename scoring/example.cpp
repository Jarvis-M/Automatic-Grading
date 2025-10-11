#include <iostream>
using namespace std;
int main() {
    long long a, b;
    cout << "请输入两个整数: ";
    cin >> a >> b;
    long long sum = a - b;
    cout << "它们的和是: " << sum << endl;
    return 0;
}