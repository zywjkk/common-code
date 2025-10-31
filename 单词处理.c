#include<stdio.h>
int main(){
    char c;int isword=0,wordlen=0,num=0;
    while ((c=getchar())!='\n'){
        if (c==' ' || c=='\t' || c=='\v' || c=='\r'){
            if (wordlen!=0){
                printf(" %d\n",wordlen);
                num++;
            }
            isword=wordlen=0;
        }else {
            if('a' <= c && c <= 'z' && isword == 0) {  // 小写首字母，转为大写
                c = c - 'a' + 'A';
                putchar(c);
                isword = 1;// 后续字符不是首字母
                wordlen++;
            } else {  // 非首字母的字母或其他字符，直接输出
                putchar(c);
                isword = 1;
                wordlen++;
            }
        }
    }
    if (wordlen!=0){
    printf(" %d\n",wordlen);
    printf("count = %d",num+1);
    }else{
    printf("count = %d",num);
    }
    return 0;
}
