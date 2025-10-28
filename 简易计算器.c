#include <stdio.h>
/// @brief 简单计算器，支持加减乘除运算，输入格式如 12+34*2-5/3=29.优先级位左至右，无算数优先级。
/// @return 
int main() {
    char c;
    int result = 0, num = 0;
    char op = '+';  // 初始运算符设为+，用于处理第一个操作数
    int is_valid = 1;  // 标记是否合法

    // 读取第一个操作数
    while ((c = getchar()) != '+' && c != '-' && c != '*' && c != '/' && c != '=') {
        if (c < '0' || c > '9') {  // 非法字符
            is_valid = 0;
            break;
        }
        num = num * 10 + (c - '0');
    }
    if (!is_valid) {
        printf("ERROR\n");
        return 0;
    }
    result = num;  // 第一个操作数赋值给result
    num = 0;       // 重置num，用于存储下一个操作数

    // 处理后续的运算符和操作数
    while (c != '=') {
        op = c;  // 记录当前运算符
        // 读取下一个操作数
        while ((c = getchar()) != '+' && c != '-' && c != '*' && c != '/' && c != '=') {
            if (c < '0' || c > '9') {  // 非法字符
                is_valid = 0;
                break;
            }
            num = num * 10 + (c - '0');
        }
        if (!is_valid) {
            printf("ERROR\n");
            return 0;
        }

        // 根据运算符执行运算
        switch (op) {
            case '+':
                result += num;
                break;
            case '-':
                result -= num;
                break;
            case '*':
                result *= num;
                break;
            case '/':
                if (num == 0) {  // 分母为0
                    is_valid = 0;
                    break;
                }
                result /= num;
                break;
            default:  // 非法运算符
                is_valid = 0;
                break;
        }
        if (!is_valid) {
            printf("ERROR\n");
            return 0;
        }
        num = 0;  // 重置num，准备下一个操作数
    }

    // 输出结果
    printf("%d\n", result);
    return 0;
}