// 들여쓰기 수정 검증 스크립트 - 브라우저 콘솔에서 실행
console.log('=== 들여쓰기 수정 검증 ===');

// 1. CSS 변수 값 확인
const rootStyle = getComputedStyle(document.documentElement);
const indentValue = rootStyle.getPropertyValue('--file-tree-indent-per-level').trim();
console.log('✅ CSS 변수 값:', indentValue);

// 2. 화면 크기별 예상 값 확인
const screenWidth = window.innerWidth;
let expectedValue;
if (screenWidth >= 1024) {
  expectedValue = '4px';
} else if (screenWidth >= 768) {
  expectedValue = '3px';
} else {
  expectedValue = '2px';
}

console.log(`📱 화면 크기: ${screenWidth}px, 예상값: ${expectedValue}, 실제값: ${indentValue}`);

// 3. 실제 DOM 요소들의 들여쓰기 확인
const depth0Elements = document.querySelectorAll('.file-tree-depth-0');
const depth1Elements = document.querySelectorAll('.file-tree-depth-1');

console.log(`📊 요소 개수: depth-0 = ${depth0Elements.length}, depth-1 = ${depth1Elements.length}`);

// 4. 실제 적용된 margin-left 값 확인
if (depth1Elements.length > 0) {
  const firstDepth1 = depth1Elements[0];
  const computedMargin = getComputedStyle(firstDepth1).marginLeft;
  console.log(`🎯 depth-1 요소의 실제 margin-left: ${computedMargin}`);
  
  // 예상 값과 비교
  const expectedMargin = `calc(${indentValue} * 1)`;
  console.log(`🔄 계산된 예상값: ${indentValue} * 1 = ${parseInt(indentValue) * 1}px`);
  
  if (computedMargin === `${parseInt(indentValue) * 1}px`) {
    console.log('✅ 들여쓰기가 정상적으로 적용됨!');
  } else {
    console.log('❌ 들여쓰기 적용 실패');
    console.log('디버깅 정보:');
    console.log('  - CSS 클래스:', firstDepth1.className);
    console.log('  - 인라인 스타일:', firstDepth1.style.cssText);
  }
} else {
  console.log('⚠️ depth-1 요소가 없습니다. deps 폴더를 열어주세요.');
}

// 5. 전체 시각적 확인을 위한 임시 스타일
console.log('🎨 시각적 확인을 위해 임시 배경색 적용...');
document.querySelectorAll('.file-tree-depth-1').forEach(el => {
  el.style.backgroundColor = 'rgba(255, 0, 0, 0.1)'; // 연한 빨간색 배경
});

setTimeout(() => {
  document.querySelectorAll('.file-tree-depth-1').forEach(el => {
    el.style.backgroundColor = ''; // 3초 후 제거
  });
  console.log('🧹 임시 배경색 제거됨');
}, 3000);

console.log('=== 검증 완료 ===');