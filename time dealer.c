#include <stdio.h>
int MonthDays(int year, int month);
int main()
{
    int year,mon,day,n,daymax,a;
    scanf("%d%d%d%d",&year,&mon,&day,&n);
    daymax=MonthDays(year,mon);
    if (year<1) printf("Invalid year: %d",year);
    else if (mon<1 || mon>12) printf("Invalid month: %d",mon);
    else if (day<1 || day>daymax) printf("Invalid day: %d",day);
    else if (n<0) printf("Invalid past days: %d",n);
    else{
        a=day+n;
        while (1){
            if (a<=daymax){
                day=a;break;}
            a-=daymax;
            mon+=1;
            if (mon==13){
                mon=1;year+=1;
            }
            daymax=MonthDays(year,mon);
        }
        printf("%d days later, it is %d/%d/%d.",n,year,mon,day);
    }
        return 0;
}

int MonthDays(int year, int month){
int x;
    if ((year%4==0 && year%100!=0) || year%400==0){
        switch (month){
            case 1:case 3:case 5:case 7:case 8:case 10:case 12:x=31;break;
            case 2:x=29;break;
            default:x=30;break;
        }
    }else{
            switch (month){
            case 1:case 3:case 5:case 7:case 8:case 10:case 12:x=31;break;
            case 2:x=28;break;
            default:x=30;break;
    }}
return x;
}