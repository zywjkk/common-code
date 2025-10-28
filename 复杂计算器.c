/*，实现一个字符串表达式计算器，支持以下功能：
1. 变量赋值（变量一定是 26 个字母之中的，区分大小写）
2. 基本数学运算，包含加减乘除和指数运算（+、-、*、/、^）
3. 输出表达式的值
二、输入格式： 表达式可以是多行赋值语句（如 a=5+3）或计算表达式（如 2*a+1），以 @ 结束输入。
三、输出格式： 对于每个计算表达式输出一行计算结果（保留两位小数），对于赋值语句不输出结果。
*/
#include <stdio.h>
#include <math.h>
//暂时只学了这俩也能冲！！ 
// 变量存储数组（区分大小写）这步是偷的AI，不然不会啊哈哈 
double variables[52]; // 0-25: a-z, 26-51: A-Z

// 将字符转换为变量索引（好思路） 
int charToIndex(char c) {
    if (c >= 'a' && c <= 'z') {
        return c - 'a';
    } else if (c >= 'A' && c <= 'Z') {
        return c - 'A' + 26;
    }
    return -1; // 无效字符
}

// 获取操作数的值（数字或变量）（被迫使用指针） 
double getValue(char* expr, int* pos) {
    double result = 0.0;
    
    // 如果是数字
    if (expr[*pos] >= '0' && expr[*pos] <= '9') {
        while (expr[*pos] >= '0' && expr[*pos] <= '9') {
            result = result * 10 + (expr[*pos] - '0');
            (*pos)++;
        }
        // 处理小数部分
        if (expr[*pos] == '.') {
            (*pos)++;
            double fraction = 0.1;
            while (expr[*pos] >= '0' && expr[*pos] <= '9') {
                result += (expr[*pos] - '0') * fraction;
                fraction *= 0.1;
                (*pos)++;
            }
        }
    }
    // 如果是变量
    else if ((expr[*pos] >= 'a' && expr[*pos] <= 'z') || 
             (expr[*pos] >= 'A' && expr[*pos] <= 'Z')) {
        int index = charToIndex(expr[*pos]);
        result = variables[index];
        (*pos)++;
    }
    
    return result;
}

// 处理乘除、指数运算
double term(char* expr, int* pos) {
    double result = getValue(expr, pos);
    
    while (expr[*pos] == '*' || expr[*pos] == '/' || expr[*pos] == '^') {
        char op = expr[*pos];
        (*pos)++;
        double next = getValue(expr, pos);
        
        if (op == '*') {
            result *= next;
        } else if (op == '/') {
            if (next != 0) {
                result /= next;
            }
        } else if (op == '^') {
            result = pow(result, next);
        }
    }
    
    return result;
}

// 处理加减运算
double expression(char* expr, int* pos) {
    double result = term(expr, pos);
    
    while (expr[*pos] == '+' || expr[*pos] == '-') {
        char op = expr[*pos];
        (*pos)++;
        double next = term(expr, pos);
        
        if (op == '+') {
            result += next;
        } else {
            result -= next;
        }
    }
    
    return result;
}

// 解析并计算表达式
double evaluate(char* expr) {
    int pos = 0;
    return expression(expr, &pos);
}

int main() {
    char input[100];
    
    // 初始化变量
    for (int i = 0; i < 52; i++) {
        variables[i] = 0.0;
    }
    
    while (1) {
        fgets(input, sizeof(input), stdin);
        
        // 移除换行符
        int len = 0;
        while (input[len] != '\n' && input[len] != '\0') {
            len++;
        }
        input[len] = '\0';
        
        // 检查结束标记
        if (input[0] == '@') {
            break;
        }
        
        // 检查是否是赋值语句
        int hasAssignment = 0;
        char varName = '\0';
        
        for (int i = 0; input[i] != '\0'; i++) {
            if (input[i] == '=') {
                hasAssignment = 1;
                varName = input[i-1]; // 等号前的字符是变量名
                break;
            }
        }
        
        if (hasAssignment) {
            // 找到等号位置
            int equalPos = 0;
            while (input[equalPos] != '=') {
                equalPos++;
            }
            
            // 计算等号右边的表达式
            double value = evaluate(&input[equalPos + 1]);
            
            // 存储到变量
            int index = charToIndex(varName);
            if (index != -1) {
                variables[index] = value;
            }
        } else {
            // 直接计算表达式
            double result = evaluate(input);
            printf("%.2f\n", result);
        }
    }
    
    return 0;
}
