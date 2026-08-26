import io.github.bonigarcia.wdm.WebDriverManager;
import org.junit.Assert;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.edge.EdgeDriver;

    public class SeleniumDemo {
    static WebDriver driver;

    public static void main(String[] args) throws InterruptedException {
        driverSetup();
        gotosite();
        performLogin();
        verifylogin();
    }
        public static void driverSetup(){
            WebDriverManager.edgedriver().clearDriverCache().driverVersion("151.0.4129.78").setup();
            driver = new EdgeDriver();
            driver.manage().window().maximize();
        }

        public static void gotosite(){
            driver.get("https://ecommerce.tealiumdemo.com/");
            String title = driver.getTitle();
            System.out.println(title);
            WebElement popup1= driver.findElement(By.xpath("//div[@class='close_btn_thick']"));
            popup1.click();
        }


        public static void performLogin() throws InterruptedException {
            WebElement account= driver.findElement(By.xpath("//a[@class='skip-link skip-account']"));
            account.click();
            Thread.sleep(2000);
            WebElement login= driver.findElement(By.xpath("//a[@title='Log In']"));
            login.click();
            Thread.sleep(2000);
            WebElement popup2= driver.findElement(By.xpath("//div[@class='close_btn_thick']"));
            popup2.click();
            Thread.sleep(1000);
            WebElement email= driver.findElement(By.id("email"));
            email.sendKeys("selenium@demo.com");
            Thread.sleep(1000);
            WebElement password= driver.findElement(By.id("pass"));
            password.sendKeys("1234567");
            Thread.sleep(1000);
            WebElement submit= driver.findElement(By.id("send2"));
            submit.click();
            Thread.sleep(1000);
            WebElement popup3= driver.findElement(By.xpath("//div[@class='close_btn_thick']"));
            popup3.click();
            Thread.sleep(1000);
            WebElement accessories= driver.findElement(By.xpath("//a[@class='level0 has-children'][normalize-space()='Accessories']"));
            accessories.click();
            Thread.sleep(1000);
            WebElement popup4= driver.findElement(By.xpath("//div[@class='close_btn_thick']"));
            popup4.click();
            Thread.sleep(1000);
            WebElement sunglass= driver.findElement(By.xpath("//li[2]//div[1]//div[3]//button[1]"));
            sunglass.click();
            Thread.sleep(1000);
            WebElement popup5= driver.findElement(By.xpath("//div[@class='close_btn_thick']"));
            popup5.click();
            Thread.sleep(1000);



        }

        public static void verifylogin() throws InterruptedException {
            Thread.sleep(2000);
            System.out.println("Verifying login.....");
            String welcome = driver.findElement(By.xpath("//strong[contains(text(),'Hello, Selenium')]")).getText();
            try{
                Assert.assertEquals("Hello, Selenium Prasad Demo!",welcome);
                System.out.println("Assertion Successfull");
            }catch (Exception e){
                driver.quit();
                System.out.println("Assertion Failed");
            }


//        if (welcome.equals("Hello, Selenium Prasad Demo!")){
//            System.out.println("Login Successful");
//        }else{
//            System.out.println("Login Failed");
        }
    }


