import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import quote

class NaverBlogCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }

    def search_blogs(self, keyword, post_count=30):
        results = []
        encoded_keyword = quote(keyword)
        url = f'https://search.naver.com/search.naver?ssc=tab.blog.all&sm=tab_jum&query={encoded_keyword}'
        
        try:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            blog_lists = soup.select('div.api_subject_bx ul > li')
            
            for blog in blog_lists[:post_count]:
                try:
                    # 링크 추출
                    title_element = blog.select_one('div.detail_box > div.title_area > a')
                    link = title_element.get('href') if title_element else ''
                    
                    # 네이버 블로그 URL이 아니면 건너뛰기
                    if not link or 'blog.naver.com' not in link:
                        continue
                    
                    # 제목 추출
                    title = ''.join(title_element.stripped_strings) if title_element else ''
                    
                    # 작성자 추출
                    author_element = blog.select_one('div.user_box > div.user_box_inner > div > a')
                    author = author_element.text.strip() if author_element else ''
                    
                    # 작성일 추출
                    date_element = blog.select_one('div.user_box > div.user_box_inner > div > span')
                    date = date_element.text.strip() if date_element else ''
                    
                    # 본문 내용 가져오기
                    content = self.get_blog_content(link)
                    
                    blog_data = {
                        '번호': len(results) + 1,
                        '제목': title,
                        '작성자': author,
                        '작성일': date,
                        '링크': link,
                        '본문': content
                    }
                    
                    results.append(blog_data)
                    
                except Exception as e:
                    st.error(f"블로그 항목 처리 중 오류: {str(e)}")
                    continue
                    
        except Exception as e:
            st.error(f"페이지 가져오기 실패: {str(e)}")
            
        return pd.DataFrame(results)

    def get_blog_content(self, url):
        try:
            # 블로그 URL을 모바일 버전으로 변경
            if 'blog.naver.com' in url:
                url = url.replace('blog.naver.com', 'm.blog.naver.com')
            
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            if 'm.blog.naver.com' in url:
                # 본문의 모든 텍스트 컴포넌트들 추출
                main_container = soup.select_one('#viewTypeSelector > div > div.se-main-container')
                if main_container:
                    # 텍스트 컴포넌트와 이미지 설명 모두 추출
                    text_components = main_container.select('div.se-component.se-text, div.se-component.se-image div.se-caption')
                    content = '\n\n'.join([comp.text.strip() for comp in text_components if comp.text.strip()])
                    return content
                else:
                    # 구버전 블로그 형식 처리
                    old_content = soup.select_one('div#viewTypeSelector, div.se_component_wrap')
                    if old_content:
                        return old_content.text.strip()
            
            return ''
            
        except Exception as e:
            st.error(f"블로그 본문 가져오기 실패: {str(e)}")
            return ''

def main():
    st.set_page_config(page_title="네이버 블로그 크롤러", page_icon="📝", layout="wide")
    
    st.title("네이버 블로그 크롤링 서비스")
    st.markdown("""
    키워드를 입력하면 네이버 블로그의 게시글 정보를 수집합니다.
    수집된 데이터는 CSV 파일로 다운로드할 수 있습니다.
    """)
    
    st.markdown("### 📌 사용 방법")
    st.markdown("""
    1. 검색하고 싶은 키워드를 입력창에 입력하세요.
    2. 수집할 게시글 수를 선택하세요.
    3. '데이터 수집 시작' 버튼을 클릭하세요.
    4. 크롤링이 완료되면 결과를 확인하고 CSV 파일로 다운로드할 수 있습니다.
    
    ⚠️ 네이버 블로그 URL이 아닌 게시글은 제외하고 수집하므로, 요청하신 수집 수량과 실제 수집된 수량이 다를 수 있습니다.
    """)
    
    keyword = st.text_input("검색 키워드를 입력하세요", "")
    num_posts = st.slider("수집할 게시글 수", min_value=1, max_value=50, value=30)
    
    if st.button("데이터 수집 시작"):
        if keyword:
            try:
                crawler = NaverBlogCrawler()
                with st.spinner('데이터를 수집하고 있습니다...'):
                    df = crawler.search_blogs(keyword, num_posts)
                    
                st.success(f'총 {len(df)}개의 블로그 포스트를 수집했습니다!')
                
                st.dataframe(df)
                
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="CSV 파일 다운로드",
                    data=csv,
                    file_name=f'naver_blog_{keyword}.csv',
                    mime='text/csv'
                )
                
            except Exception as e:
                st.error(f'데이터 수집 중 오류가 발생했습니다: {str(e)}')
        else:
            st.warning('키워드를 입력해주세요.')
    
    st.markdown("---")
    st.markdown("© 2024 네이버 블로그 크롤링 서비스")

if __name__ == "__main__":
    main() 